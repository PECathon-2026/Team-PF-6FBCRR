"""Unified privacy detection engine."""
from typing import List, Dict, Tuple, Optional
from app.models import (
    DOMElement, SensitiveSpan, SensitiveCategory, BoundingBox
)
from .aadhaar import detect_aadhaar
from .pan import detect_pan
from .card import detect_cards, detect_cvv
from .contact import detect_emails, detect_phones
from .otp import detect_otp
from .secrets import detect_secrets
from .network import detect_ips
from .contextual import detect_dom_context

class DetectionEngine:
    def __init__(self):
        self._token_counters: Dict[str, int] = {}
        self._vault_mapping: Dict[str, str] = {}  # token -> original value
        self._reverse_vault: Dict[str, str] = {}  # original value -> token

    def reset_tokens(self):
        self._token_counters.clear()
        self._vault_mapping.clear()
        self._reverse_vault.clear()

    def get_token(self, category: SensitiveCategory, original_value: Optional[str]) -> str:
        """Returns or creates a stable token for an original value in this session."""
        cat_str = category.value
        if original_value and original_value in self._reverse_vault:
            return self._reverse_vault[original_value]
            
        count = self._token_counters.get(cat_str, 0) + 1
        self._token_counters[cat_str] = count
        token = f"[REDACTED:{cat_str}:{count}]"
        
        if original_value:
            self._vault_mapping[token] = original_value
            self._reverse_vault[original_value] = token
            
        return token

    def get_original(self, token: str) -> Optional[str]:
        return self._vault_mapping.get(token)

    def scan_text(self, text: str, element_id: Optional[str] = None, bbox: Optional[BoundingBox] = None) -> List[SensitiveSpan]:
        """Scans arbitrary text with all pattern detectors."""
        if not text:
            return []
            
        candidates: List[Tuple[int, int, str, SensitiveCategory, float, str, str]] = []
        
        # 1. Aadhaar
        for start, end, val, conf, reason in detect_aadhaar(text):
            candidates.append((start, end, val, SensitiveCategory.AADHAAR, conf, "AADHAAR_DETECTOR", reason))
            
        # 2. PAN
        for start, end, val, conf, reason in detect_pan(text):
            candidates.append((start, end, val, SensitiveCategory.PAN, conf, "PAN_DETECTOR", reason))
            
        # 3. Cards & CVV
        for start, end, val, conf, reason in detect_cards(text):
            candidates.append((start, end, val, SensitiveCategory.CREDIT_CARD, conf, "CARD_DETECTOR", reason))
        for start, end, val, conf, reason in detect_cvv(text):
            candidates.append((start, end, val, SensitiveCategory.CVV, conf, "CVV_DETECTOR", reason))
            
        # 4. Email & Phone
        for start, end, val, conf, reason in detect_emails(text):
            candidates.append((start, end, val, SensitiveCategory.EMAIL, conf, "EMAIL_DETECTOR", reason))
        for start, end, val, conf, reason in detect_phones(text):
            candidates.append((start, end, val, SensitiveCategory.PHONE, conf, "PHONE_DETECTOR", reason))
            
        # 5. OTP
        for start, end, val, conf, reason in detect_otp(text):
            candidates.append((start, end, val, SensitiveCategory.OTP, conf, "OTP_DETECTOR", reason))
            
        # 6. Secrets & API Keys & JWTs & PEM
        for start, end, val, cat, conf, reason in detect_secrets(text):
            candidates.append((start, end, val, cat, conf, "SECRET_DETECTOR", reason))
            
        # 7. IP Addresses
        for start, end, val, conf, reason in detect_ips(text):
            candidates.append((start, end, val, SensitiveCategory.IP_ADDRESS, conf, "NETWORK_DETECTOR", reason))
            
        # 8. Known Vault Secrets (redacts any reflected vault secrets in DOM text)
        from app.privacy.vault import vault
        for alias in vault.list_aliases():
            sec = vault.get_secret(alias)
            if sec and len(sec) >= 3 and sec in text:
                start = 0
                while True:
                    idx = text.find(sec, start)
                    if idx == -1:
                        break
                    cat = SensitiveCategory.NAME if "name" in alias else (
                        SensitiveCategory.ADDRESS if "address" in alias else (
                            SensitiveCategory.CREDIT_CARD if "card" in alias or "expiry" in alias else (
                                SensitiveCategory.CVV if "cvv" in alias else (
                                    SensitiveCategory.PASSWORD if "pass" in alias else (
                                        SensitiveCategory.EMAIL if "email" in alias else SensitiveCategory.API_KEY
                                    )
                                )
                            )
                        )
                    )
                    candidates.append((idx, idx + len(sec), sec, cat, 1.0, "VAULT_SECRET_DETECTOR", f"Vault secret matching alias {alias}"))
                    start = idx + len(sec)
            
        # Sort by start offset ascending, length descending
        candidates.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        
        # Merge overlapping spans (highest confidence / longest span wins)
        merged_spans: List[SensitiveSpan] = []
        last_end = -1
        
        for start, end, val, category, conf, det_name, reason in candidates:
            if start < last_end:
                continue  # Overlap with previously accepted span
            last_end = end
            token = self.get_token(category, val)
            merged_spans.append(SensitiveSpan(
                category=category,
                text=val,
                start=start,
                end=end,
                confidence=conf,
                detector=det_name,
                reason=reason,
                replacement_token=token,
                element_id=element_id,
                bbox=bbox,
            ))
            
        return merged_spans

    def analyze_dom(self, elements: List[DOMElement]) -> Tuple[List[SensitiveSpan], Dict[str, str]]:
        """
        Analyzes a list of DOM elements.
        Returns:
            - List of all detected SensitiveSpan objects
            - Mapping of element_id -> sanitized text
        """
        all_spans: List[SensitiveSpan] = []
        element_sanitized_text: Dict[str, str] = {}
        
        # 1. Structural DOM inspection
        structural_spans = detect_dom_context(elements)
        structural_el_ids = set()
        for span in structural_spans:
            token = self.get_token(span.category, span.text)
            span.replacement_token = token
            all_spans.append(span)
            if span.element_id:
                structural_el_ids.add(span.element_id)
                element_sanitized_text[span.element_id] = token
                
        # 2. Textual pattern inspection across elements
        for el in elements:
            combined_text = f"{el.text} {el.value}".strip()
            if not combined_text:
                continue
                
            spans = self.scan_text(combined_text, element_id=el.id, bbox=el.bbox)
            if spans:
                all_spans.extend(spans)
                # Reconstruct sanitized text replacing sensitive spans
                sanitized = combined_text
                for s in sorted(spans, key=lambda x: x.start or 0, reverse=True):
                    if s.start is not None and s.end is not None:
                        sanitized = sanitized[:s.start] + s.replacement_token + sanitized[s.end:]
                element_sanitized_text[el.id] = sanitized
            elif el.id not in element_sanitized_text:
                element_sanitized_text[el.id] = combined_text
                
        return all_spans, element_sanitized_text
