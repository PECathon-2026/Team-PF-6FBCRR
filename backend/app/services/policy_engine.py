from typing import Tuple, List, Optional
from app.models.schemas import (
    SensitivityCategory,
    DisclosureDecision,
    TransformationType,
    TaskSession,
)


class PolicyEngine:
    """
    Task-Scoped Disclosure Engine.
    Enforces the user's declared disclosure boundaries throughout an AI task.
    Determines whether a detected sensitive data item is necessary for the authorized task,
    irrelevant, or strictly forbidden. Never relies on LLM self-attestation.
    """

    # Immutable hard rules: Categories that can NEVER be transmitted raw to an external entity
    HARD_BLOCKED_CATEGORIES = {
        SensitivityCategory.CANARY,
        SensitivityCategory.SYSTEM_SECRET,
        SensitivityCategory.CREDENTIAL,
    }

    def evaluate_disclosure(
        self,
        task: TaskSession,
        category: SensitivityCategory,
        entity_text: str,
        purpose: str = "ai_task_planning",
        destination: str = "EXTERNAL_AI"
    ) -> Tuple[DisclosureDecision, TransformationType, str, str]:
        """
        Evaluates a disclosure request against task scope, destination, and category.
        Returns:
            (Decision, TransformationType, TransformedValue, Justification)
        """
        # Invariant 1: Synthetic canary tokens must never leak under any circumstance
        if category == SensitivityCategory.CANARY:
            return (
                DisclosureDecision.BLOCK,
                TransformationType.REDACT_FULL,
                "[BLOCKED_CANARY_SECRET]",
                "Synthetic canary secret blocked by outbound boundary rule."
            )

        # Invariant 2: Passwords, tokens, bearer keys must never be transmitted raw to external AI
        if category in (SensitivityCategory.CREDENTIAL, SensitivityCategory.SYSTEM_SECRET):
            return (
                DisclosureDecision.BLOCK,
                TransformationType.REDACT_FULL,
                f"[REDACTED_{category.value}]",
                f"Hard policy forbids outbound disclosure of {category.value} to {destination}."
            )

        # Invariant 3: Financial data (Credit cards, CVV, bank routing)
        if category == SensitivityCategory.FINANCIAL:
            # Check if current task explicitly has authorized financial scope
            has_payment_scope = any(
                scope in ["payment", "checkout", "billing_verification"]
                for scope in task.allowed_scopes
            )
            is_prohibited = any(
                scope in ["payment", "financial_transaction"]
                for scope in task.prohibited_scopes
            )

            if is_prohibited or not has_payment_scope:
                return (
                    DisclosureDecision.BLOCK,
                    TransformationType.REDACT_FULL,
                    "[REDACTED_FINANCIAL]",
                    "Financial data is not authorized under the active task scope."
                )

            # If authorized for verification, minimize by masking all but last 4 digits
            digits = "".join(filter(str.isdigit, entity_text))
            last4 = digits[-4:] if len(digits) >= 4 else "0000"
            return (
                DisclosureDecision.MINIMIZE,
                TransformationType.REDACT_PARTIAL,
                f"****-****-****-{last4}",
                "Financial data minimized to last 4 digits for authorized verification."
            )

        # Invariant 4: Direct PII (SSN, Passport, Full National ID)
        if category == SensitivityCategory.PII_DIRECT:
            return (
                DisclosureDecision.BLOCK,
                TransformationType.REDACT_FULL,
                "[REDACTED_GOVERNMENT_ID]",
                "Direct government identifiers are blocked from external AI ingestion."
            )

        # Invariant 5: Indirect PII (Email, Phone, Name, Address)
        if category == SensitivityCategory.PII_INDIRECT:
            # Check if task goal requires identity verification or order lookup
            has_identity_scope = any(
                scope in ["order_retrieval", "view_receipt", "user_profile", "booking_lookup"]
                for scope in task.allowed_scopes
            )

            if not has_identity_scope:
                return (
                    DisclosureDecision.BLOCK,
                    TransformationType.REDACT_FULL,
                    "[REDACTED_PII]",
                    "Personal identifier is irrelevant to the active task goal."
                )

            # If necessary, minimize rather than leaking full raw value
            if "@" in entity_text:
                # Email minimization: j***@example.com
                parts = entity_text.split("@")
                username = parts[0]
                domain = parts[1] if len(parts) > 1 else ""
                masked_user = (username[0] + "***") if username else "***"
                return (
                    DisclosureDecision.MINIMIZE,
                    TransformationType.REDACT_PARTIAL,
                    f"{masked_user}@{domain}",
                    "Email minimized to protect user identity while preserving domain context."
                )
            elif any(c.isdigit() for c in entity_text) and len(entity_text) >= 7:
                # Phone minimization: ***-***-1234
                digits = "".join(filter(str.isdigit, entity_text))
                last4 = digits[-4:] if len(digits) >= 4 else "0000"
                return (
                    DisclosureDecision.MINIMIZE,
                    TransformationType.REDACT_PARTIAL,
                    f"***-***-{last4}",
                    "Phone number minimized to last 4 digits."
                )
            else:
                return (
                    DisclosureDecision.MINIMIZE,
                    TransformationType.REDACT_PARTIAL,
                    "[ANONYMIZED_USER]",
                    "User identity generalized for privacy preservation."
                )

        # Invariant 6: Health information
        if category == SensitivityCategory.HEALTH:
            return (
                DisclosureDecision.BLOCK,
                TransformationType.REDACT_FULL,
                "[REDACTED_HEALTH_RECORD]",
                "Protected health information blocked by default policy."
            )

        # Default for non-sensitive data
        return (
            DisclosureDecision.ALLOW,
            TransformationType.PASSTHROUGH,
            entity_text,
            "Non-sensitive data necessary for task execution."
        )


policy_engine = PolicyEngine()
