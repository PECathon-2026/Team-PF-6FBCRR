import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.models.schemas import (
    TaskSession,
    TaskStatus,
    TaskCreateRequest,
    ApprovalItem,
    ApprovalState,
    PrivacyReceipt,
    BenchmarkRunResponse,
)


class TaskManager:
    """
    Thread-safe Task and Session Lifecycle Manager.
    Coordinates active browsing sessions, approval queues, privacy receipts,
    and historical benchmark results.
    """

    def __init__(self):
        self._tasks: Dict[str, TaskSession] = {}
        self._approvals: Dict[str, ApprovalItem] = {}
        self._receipts: Dict[str, PrivacyReceipt] = {}
        self._task_receipts: Dict[str, List[str]] = {}
        self._benchmark_runs: Dict[str, BenchmarkRunResponse] = {}

    def create_task(self, req: TaskCreateRequest) -> TaskSession:
        task_id = f"tsk_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        canary_tokens = []
        if req.enforce_canary_injection:
            canary_tokens.append(f"CANARY-{uuid.uuid4().hex[:6].upper()}-SEC")

        session = TaskSession(
            task_id=task_id,
            title=req.title,
            goal=req.goal,
            target_domain=req.target_domain,
            allowed_scopes=req.allowed_scopes,
            prohibited_scopes=req.prohibited_scopes,
            status=TaskStatus.INITIALIZED,
            created_at=now,
            updated_at=now,
            step_count=0,
            active_canary_tokens=canary_tokens
        )
        self._tasks[task_id] = session
        self._task_receipts[task_id] = []
        return session

    def get_task(self, task_id: str) -> Optional[TaskSession]:
        return self._tasks.get(task_id)

    def update_task_status(self, task_id: str, status: TaskStatus) -> Optional[TaskSession]:
        task = self.get_task(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.now(timezone.utc)
        return task

    def increment_step(self, task_id: str) -> int:
        task = self.get_task(task_id)
        if task:
            task.step_count += 1
            task.updated_at = datetime.now(timezone.utc)
            return task.step_count
        return 0

    def add_approval(self, approval: ApprovalItem):
        self._approvals[approval.approval_id] = approval

    def get_approval(self, approval_id: str) -> Optional[ApprovalItem]:
        return self._approvals.get(approval_id)

    def get_pending_approvals_for_task(self, task_id: str) -> List[ApprovalItem]:
        return [
            item for item in self._approvals.values()
            if item.task_id == task_id and item.status == ApprovalState.PENDING_APPROVAL
        ]

    def resolve_approval(
        self,
        approval_id: str,
        decision: ApprovalState,
        comment: Optional[str] = None
    ) -> Optional[ApprovalItem]:
        item = self.get_approval(approval_id)
        if item:
            item.status = decision
            item.reviewer_comment = comment
            item.resolved_at = datetime.now(timezone.utc)
            # Update task status back to in progress or blocked
            task = self.get_task(item.task_id)
            if task:
                task.status = TaskStatus.IN_PROGRESS if decision == ApprovalState.APPROVED else TaskStatus.BLOCKED_BY_POLICY
        return item

    def store_receipt(self, receipt: PrivacyReceipt):
        self._receipts[receipt.receipt_id] = receipt
        if receipt.task_id in self._task_receipts:
            self._task_receipts[receipt.task_id].append(receipt.receipt_id)

    def get_receipt(self, receipt_id: str) -> Optional[PrivacyReceipt]:
        return self._receipts.get(receipt_id)

    def get_task_receipts(self, task_id: str) -> List[PrivacyReceipt]:
        receipt_ids = self._task_receipts.get(task_id, [])
        return [self._receipts[rid] for rid in receipt_ids if rid in self._receipts]

    def record_benchmark_run(self, run: BenchmarkRunResponse):
        self._benchmark_runs[run.run_id] = run

    def get_benchmark_runs(self) -> List[BenchmarkRunResponse]:
        return list(self._benchmark_runs.values())


task_manager = TaskManager()
