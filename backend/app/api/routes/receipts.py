import hashlib
from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel
from app.models.schemas import PrivacyReceipt
from app.services.task_manager import task_manager

router = APIRouter(tags=["Privacy Receipts & Audit Ledger"])


class ReceiptVerificationRequest(BaseModel):
    receipt_id: str
    payload_to_verify: str


class ReceiptVerificationResponse(BaseModel):
    receipt_id: str
    verified: bool
    computed_sha256: str
    recorded_sha256: str
    message: str


@router.get("/tasks/{task_id}/receipts", response_model=List[PrivacyReceipt])
async def list_task_receipts(task_id: str):
    """Fetches all cryptographic privacy receipts minted for a task session."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task session '{task_id}' not found."
        )
    return task_manager.get_task_receipts(task_id)


@router.get("/receipts/{receipt_id}", response_model=PrivacyReceipt)
async def get_receipt(receipt_id: str):
    """Retrieves an individual tamper-evident privacy receipt."""
    receipt = task_manager.get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Privacy receipt '{receipt_id}' not found."
        )
    return receipt


@router.post("/receipts/verify", response_model=ReceiptVerificationResponse)
async def verify_receipt_integrity(req: ReceiptVerificationRequest):
    """
    Verifies that a provided payload matches the non-repudiation SHA-256 digest
    recorded on the minted privacy receipt.
    """
    receipt = task_manager.get_receipt(req.receipt_id)
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Privacy receipt '{req.receipt_id}' not found."
        )

    computed = hashlib.sha256(req.payload_to_verify.encode("utf-8")).hexdigest()
    match = (computed == receipt.sanitized_payload_sha256)

    return ReceiptVerificationResponse(
        receipt_id=receipt.receipt_id,
        verified=match,
        computed_sha256=computed,
        recorded_sha256=receipt.sanitized_payload_sha256,
        message="Cryptographic digest match confirmed." if match else "Digest mismatch: payload does not match receipt."
    )
