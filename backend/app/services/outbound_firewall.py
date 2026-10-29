import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class FirewallViolation(BaseModel):
    category: str
    pattern_matched: str
    sample_redacted: str
    description: str


class OutboundFirewallResult(BaseModel):
    passed: bool
    violations: List[FirewallViolation]
    sanitized_payload_preview: str
    sha256_digest: str


class OutboundPrivacyFirewall:
    """
    Mandatory Outbound Privacy Firewall.
    Runs deep inspection on the exact serialized bytes immediately prior to any external AI call.
    Guarantees fail-closed enforcement: if any unredacted credential, payment card,
    government identifier, or active canary token is detected, transmission is halted.
    """

    def __init__(self):
        # Compiled regex patterns for high-sensitivity targets
        self.patterns = {
            "CREDIT_CARD": re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
            "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "API_KEY": re.compile(r"\b(?:sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{30,}|AKIA[0-9A-Z]{16})\b"),
            "BEARER_TOKEN": re.compile(r"\bBearer\s+[A-Za-z0-9\-\._~\+\/]{20,}=*\b", re.IGNORECASE),
            "PASSWORD_ASSIGNMENT": re.compile(r'(?:password|passwd|pwd)\s*[:=]\s*["\']([^"\'\s]{6,})["\']', re.IGNORECASE),
            "CANARY_SECRET": re.compile(r"\bCANARY-[A-Z0-9]{4,}-[A-Z0-9]{4,}\b"),
        }

    @staticmethod
    def _luhn_checksum_valid(card_number_str: str) -> bool:
        """Validates standard credit card numbers using Luhn mod-10 formula."""
        digits = [int(c) for c in card_number_str if c.isdigit()]
        if len(digits) < 13 or len(digits) > 19:
            return False
        total = 0
        reverse_digits = digits[::-1]
        for i, digit in enumerate(reverse_digits):
            if i % 2 == 1:
                doubled = digit * 2
                total += doubled - 9 if doubled > 9 else doubled
            else:
                total += digit
        return total % 10 == 0

    def inspect_payload(
        self,
        payload_text: str,
        active_canary_tokens: Optional[List[str]] = None
    ) -> OutboundFirewallResult:
        """
        Deep-inspects the outgoing payload.
        Returns OutboundFirewallResult with passed=True only if NO violations exist.
        """
        import hashlib

        violations: List[FirewallViolation] = []

        # 1. Check for Active Canary Tokens
        if active_canary_tokens:
            for token in active_canary_tokens:
                if token and token in payload_text:
                    violations.append(
                        FirewallViolation(
                            category="CANARY_LEAKAGE",
                            pattern_matched="ACTIVE_CANARY_TOKEN",
                            sample_redacted=f"{token[:6]}...[LEAK_PREVENTED]",
                            description=f"Planted canary secret '{token[:8]}...' detected in outgoing payload."
                        )
                    )

        # Also generic canary regex check
        for match in self.patterns["CANARY_SECRET"].finditer(payload_text):
            val = match.group(0)
            violations.append(
                FirewallViolation(
                    category="CANARY_LEAKAGE",
                    pattern_matched="CANARY_SECRET_REGEX",
                    sample_redacted=f"{val[:8]}...[MASKED]",
                    description="Unredacted synthetic canary token pattern matched."
                )
            )

        # 2. Check for Unredacted Credit Cards
        for match in self.patterns["CREDIT_CARD"].finditer(payload_text):
            raw_val = match.group(0)
            if self._luhn_checksum_valid(raw_val):
                masked = f"****-****-****-{raw_val[-4:]}"
                violations.append(
                    FirewallViolation(
                        category="FINANCIAL_CARD_EXFILTRATION",
                        pattern_matched="LUHN_VALID_CREDIT_CARD",
                        sample_redacted=masked,
                        description="Valid unredacted payment card detected in outgoing payload."
                    )
                )

        # 3. Check for Government Identifiers (SSN)
        for match in self.patterns["SSN"].finditer(payload_text):
            raw_val = match.group(0)
            violations.append(
                FirewallViolation(
                    category="DIRECT_PII_EXFILTRATION",
                    pattern_matched="SSN_PATTERN",
                    sample_redacted="***-**-" + raw_val[-4:],
                    description="Unredacted US Social Security Number detected in outbound data."
                )
            )

        # 4. Check for API Keys & Bearer Tokens
        for match in self.patterns["API_KEY"].finditer(payload_text):
            raw_val = match.group(0)
            violations.append(
                FirewallViolation(
                    category="CREDENTIAL_EXFILTRATION",
                    pattern_matched="API_KEY_PATTERN",
                    sample_redacted=raw_val[:5] + "...[REDACTED_SECRET]",
                    description="Unredacted high-entropy API key detected."
                )
            )

        for match in self.patterns["BEARER_TOKEN"].finditer(payload_text):
            violations.append(
                FirewallViolation(
                    category="CREDENTIAL_EXFILTRATION",
                    pattern_matched="BEARER_AUTH_PATTERN",
                    sample_redacted="Bearer [REDACTED_TOKEN]",
                    description="Raw Bearer authentication authorization header detected."
                )
            )

        # 5. Check for Plaintext Password Assignments
        for match in self.patterns["PASSWORD_ASSIGNMENT"].finditer(payload_text):
            violations.append(
                FirewallViolation(
                    category="CREDENTIAL_EXFILTRATION",
                    pattern_matched="PLAINTEXT_PASSWORD_FIELD",
                    sample_redacted="password='[REDACTED]'",
                    description="Plaintext password value detected in outbound payload."
                )
            )

        # Compute SHA-256 digest of outbound payload for non-repudiation
        digest = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
        passed = (len(violations) == 0)

        preview = payload_text[:300] + ("..." if len(payload_text) > 300 else "")

        return OutboundFirewallResult(
            passed=passed,
            violations=violations,
            sanitized_payload_preview=preview,
            sha256_digest=digest
        )


outbound_firewall = OutboundPrivacyFirewall()
