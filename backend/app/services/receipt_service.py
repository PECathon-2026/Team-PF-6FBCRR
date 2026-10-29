import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Optional
from app.models.schemas import (
    PrivacyReceipt,
    ApprovalState,
    DetectedEntity,
)


class PrivacyReceiptService:
    """
    Cryptographic Privacy Receipts & Non-Repudiation Audit Service.
    Mints tamper-evident receipts that record privacy decisions, transformation types,
    and SHA-256 payload digests WITHOUT persisting raw secrets or unredacted PII.
    """

    def mint_receipt(
        self,
        task_id: str,
        step_index: int,
        destination_category: str,
        detected_entities: List[DetectedEntity],
        sanitized_payload_text: str,
        approval_state: ApprovalState,
        enforcement_outcome: str = "SAFE_TRANSMISSION",
        benchmark_run_id: Optional[str] = None
    ) -> PrivacyReceipt:
        receipt_id = f"rcpt_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        # Categorize decisions and transformations applied
        categories_detected = list({e.entity_type.value for e in detected_entities})
        decisions_applied: Dict[str, str] = {
            e.entity_type.value: e.decision.value for e in detected_entities
        }
        transformations_applied = list({e.transformation.value for e in detected_entities})

        # Non-repudiation cryptographic digest of final egress payload
        payload_sha256 = hashlib.sha256(sanitized_payload_text.encode("utf-8")).hexdigest()

        return PrivacyReceipt(
            receipt_id=receipt_id,
            task_id=task_id,
            step_index=step_index,
            timestamp=now,
            policy_version="2026.1-task-scoped",
            destination_category=destination_category,
            detected_categories=categories_detected,
            decisions_applied=decisions_applied,
            transformations_applied=transformations_applied,
            enforcement_outcome=enforcement_outcome,
            approval_state=approval_state,
            sanitized_payload_sha256=payload_sha256,
            benchmark_run_id=benchmark_run_id
        )


receipt_service = PrivacyReceiptService()
