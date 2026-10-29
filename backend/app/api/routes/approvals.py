from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.schemas import (
    ApprovalItem,
    ApprovalDecisionRequest,
    ApprovalState,
)
from app.services.task_manager import task_manager

router = APIRouter(tags=["Human Approvals & Action Oversight"])


@router.get("/tasks/{task_id}/approvals", response_model=List[ApprovalItem])
async def list_pending_approvals(task_id: str):
    """Retrieves all pending human approval requests for a task."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task session '{task_id}' not found."
        )
    return task_manager.get_pending_approvals_for_task(task_id)


@router.get("/approvals/{approval_id}", response_model=ApprovalItem)
async def get_approval(approval_id: str):
    """Retrieves details of a specific approval item."""
    item = task_manager.get_approval(approval_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval request '{approval_id}' not found."
        )
    return item


@router.post("/tasks/{task_id}/approvals/{approval_id}", response_model=ApprovalItem)
async def resolve_approval(task_id: str, approval_id: str, req: ApprovalDecisionRequest):
    """Submits human review decision (APPROVED or REJECTED) for a consequential action."""
    item = task_manager.get_approval(approval_id)
    if not item or item.task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval item '{approval_id}' for task '{task_id}' not found."
        )

    if req.decision not in (ApprovalState.APPROVED, ApprovalState.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be either 'APPROVED' or 'REJECTED'."
        )

    resolved = task_manager.resolve_approval(
        approval_id=approval_id,
        decision=req.decision,
        comment=req.reviewer_comment
    )
    return resolved
