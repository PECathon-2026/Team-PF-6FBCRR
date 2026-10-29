from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.schemas import (
    TaskCreateRequest,
    TaskSession,
    PlanStepRequest,
    PlanStepResponse,
    TaskStatus,
    ApprovalState,
)
from app.services.task_manager import task_manager
from app.services.policy_engine import policy_engine
from app.services.outbound_firewall import outbound_firewall
from app.services.ai_orchestrator import get_ai_provider
from app.services.action_validator import action_validator
from app.services.receipt_service import receipt_service

router = APIRouter(prefix="/tasks", tags=["Task Sessions & Planning"])


@router.post("", response_model=TaskSession, status_code=status.HTTP_201_CREATED)
async def create_task(req: TaskCreateRequest):
    """Initializes a new task session with authorized disclosure scopes."""
    session = task_manager.create_task(req)
    return session


@router.get("/{task_id}", response_model=TaskSession)
async def get_task(task_id: str):
    """Retrieves metadata and status for an existing task session."""
    session = task_manager.get_task(task_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task session '{task_id}' not found."
        )
    return session


@router.post("/{task_id}/plan", response_model=PlanStepResponse)
async def plan_task_step(task_id: str, req: PlanStepRequest):
    """
    Core Orchestration Pipeline:
    1. Verifies Task Session & Scope
    2. Applies Task-Scoped Minimization over Inbound Entities
    3. Mandatory Outbound Privacy Firewall (deep inspection of final serialized payload; fails closed)
    4. AI Orchestration with configured provider (Deterministic Mock or Cloud LLM)
    5. Independent Browser Action Validator & Consequential Approval Gating
    6. Non-Repudiation Privacy Receipt Minting
    """
    session = task_manager.get_task(task_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task session '{task_id}' not found."
        )

    # Increment step counter
    step_num = task_manager.increment_step(task_id)
    task_manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)

    # 1. Apply Task-Scoped Policy to all detected entities
    working_payload = req.sanitized_dom_text
    applied_decisions = []
    for entity in req.detected_entities:
        decision, transformation, replacement, justification = policy_engine.evaluate_disclosure(
            task=session,
            category=entity.entity_type,
            entity_text=entity.replacement,
            purpose="ai_planning",
            destination="EXTERNAL_AI"
        )
        entity.decision = decision
        entity.transformation = transformation
        entity.justification = justification

    # 2. Final Outbound Privacy Firewall Check
    # Combine active canaries from session and request
    combined_canaries = list(set(session.active_canary_tokens + req.canary_tokens_active))
    fw_result = outbound_firewall.inspect_payload(
        payload_text=working_payload,
        active_canary_tokens=combined_canaries
    )

    if not fw_result.passed:
        task_manager.update_task_status(task_id, TaskStatus.BLOCKED_BY_POLICY)
        violation_msgs = [f"[{v.category}] {v.description}" for v in fw_result.violations]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "OUTBOUND_PRIVACY_FIREWALL_VIOLATION",
                "message": "Transmission aborted: unredacted sensitive data or canary tokens detected in outgoing payload.",
                "violations": [v.model_dump() for v in fw_result.violations],
                "sha256_digest": fw_result.sha256_digest
            }
        )

    # 3. AI Planning (strictly receives firewall-inspected payload)
    ai_provider = get_ai_provider()
    proposed_action = await ai_provider.plan_action(
        task=session,
        step_index=step_num,
        sanitized_dom_text=working_payload,
        current_url=req.current_url
    )

    # 4. Independent Action Validation & Consequential Risk Classification
    validated_action, approval_state, approval_item = action_validator.validate_and_classify(
        task_id=task_id,
        step_index=step_num,
        action=proposed_action
    )

    approval_id = None
    if approval_item:
        task_manager.add_approval(approval_item)
        approval_id = approval_item.approval_id
        task_manager.update_task_status(task_id, TaskStatus.AWAITING_APPROVAL)

    # 5. Mint Tamper-Evident Privacy Receipt
    receipt = receipt_service.mint_receipt(
        task_id=task_id,
        step_index=step_num,
        destination_category="EXTERNAL_AI_ORCHESTRATOR",
        detected_entities=req.detected_entities,
        sanitized_payload_text=working_payload,
        approval_state=approval_state,
        enforcement_outcome="SAFE_TRANSMISSION"
    )
    task_manager.store_receipt(receipt)

    return PlanStepResponse(
        task_id=task_id,
        step_index=step_num,
        action=validated_action,
        approval_state=approval_state,
        approval_id=approval_id,
        receipt_id=receipt.receipt_id,
        outbound_inspection_passed=True,
        message="Step planned successfully with outbound privacy guarantees."
    )


@router.post("/{task_id}/complete", response_model=TaskSession)
async def complete_task(task_id: str):
    """Marks task session as completed."""
    session = task_manager.update_task_status(task_id, TaskStatus.COMPLETED)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task session '{task_id}' not found."
        )
    return session
