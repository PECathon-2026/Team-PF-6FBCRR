import hashlib
from app.models.schemas import (
    ApprovalState,
    DetectedEntity,
    SensitivityCategory,
    DisclosureDecision,
    TransformationType,
)
from app.services.receipt_service import receipt_service


def test_receipt_minting_and_sha256():
    raw_payload = "Sanitized receipt text with masked card ****-****-****-1234."
    detected = [
        DetectedEntity(
            entity_type=SensitivityCategory.FINANCIAL,
            decision=DisclosureDecision.MINIMIZE,
            transformation=TransformationType.REDACT_PARTIAL,
            replacement="****-****-****-1234"
        )
    ]
    receipt = receipt_service.mint_receipt(
        task_id="tsk_rec_01",
        step_index=1,
        destination_category="EXTERNAL_AI_ORCHESTRATOR",
        detected_entities=detected,
        sanitized_payload_text=raw_payload,
        approval_state=ApprovalState.NOT_REQUIRED
    )

    assert receipt.receipt_id.startswith("rcpt_")
    assert receipt.task_id == "tsk_rec_01"
    assert "FINANCIAL" in receipt.detected_categories
    assert receipt.decisions_applied["FINANCIAL"] == "MINIMIZE"

    # Verify SHA-256 digest match
    expected_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
    assert receipt.sanitized_payload_sha256 == expected_hash
