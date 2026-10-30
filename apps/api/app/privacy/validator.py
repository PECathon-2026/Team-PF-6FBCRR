"""Outbound AI Egress Gateway and Payload Validator."""
import hashlib
from typing import Tuple, List, Optional
from app.models import SanitizedObservation, AuditEventType
from app.privacy.detectors.engine import DetectionEngine
from app.privacy.screenshot import ScreenshotSanitizer
from app.privacy.vault import vault

class EgressBlockedException(Exception):
    def __init__(self, reason: str, detected_category: Optional[str] = None):
        super().__init__(reason)
        self.reason = reason
        self.detected_category = detected_category

class EgressGateway:
    def __init__(self, detector_engine: DetectionEngine, screenshot_sanitizer: ScreenshotSanitizer):
        self.detector = detector_engine
        self.screenshot_sanitizer = screenshot_sanitizer
        # Synthetic canary values for security regression testing
        self.canaries: set[str] = set()

    def register_canary(self, canary: str):
        """Registers a known synthetic canary value to test leak interception."""
        self.canaries.add(canary)

    def validate_and_gate(
        self,
        observation: SanitizedObservation,
    ) -> Tuple[bool, str]:
        """
        Deny-by-default egress gatekeeper.
        Rescans all outgoing fields for sensitive patterns, canaries, and vault secrets.
        Returns:
            (is_valid, safe_reason)
        Raises:
            EgressBlockedException if sensitive data is detected.
        """
        # 1. Schema check
        if not isinstance(observation, SanitizedObservation):
            raise EgressBlockedException("Payload rejected: not a valid SanitizedObservation schema")

        # 2. Screenshot provenance validation
        if observation.sanitized_screenshot_token:
            if not self.screenshot_sanitizer.verify_provenance(observation.provenance_hash):
                raise EgressBlockedException("Egress blocked: unverified screenshot provenance token", "PROVENANCE_FAIL")

        # 3. Check for any registered synthetic canaries in outgoing text
        for el in observation.elements:
            for canary in self.canaries:
                if canary in el.sanitized_text or (el.label and canary in el.label):
                    raise EgressBlockedException(
                        f"Egress blocked: synthetic canary detected in element {el.id}",
                        "SYNTHETIC_CANARY_LEAK"
                    )

        # 4. Check for any vault secret raw values
        for alias in vault.list_aliases():
            secret_val = vault.get_secret(alias)
            if secret_val and len(secret_val) >= 4:
                for el in observation.elements:
                    if secret_val in el.sanitized_text:
                        raise EgressBlockedException(
                            f"Egress blocked: raw vault secret value detected in outbound element {el.id}",
                            "RAW_SECRET_LEAK"
                        )

        # 5. Rescan all elements with pattern detectors (second defense layer)
        for el in observation.elements:
            spans = self.detector.scan_text(el.sanitized_text)
            if spans:
                first_span = spans[0]
                raise EgressBlockedException(
                    f"Egress blocked: detector flagged sensitive data ({first_span.category.value}) in element {el.id}",
                    first_span.category.value
                )

            if el.label:
                label_spans = self.detector.scan_text(el.label)
                if label_spans:
                    first_span = label_spans[0]
                    raise EgressBlockedException(
                        f"Egress blocked: detector flagged sensitive data ({first_span.category.value}) in label of element {el.id}",
                        first_span.category.value
                    )

        return True, "Egress validation passed: payload is sanitized and verified"
