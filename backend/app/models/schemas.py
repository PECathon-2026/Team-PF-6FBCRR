from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SensitivityCategory(str, Enum):
    CREDENTIAL = "CREDENTIAL"
    FINANCIAL = "FINANCIAL"
    PII_DIRECT = "PII_DIRECT"
    PII_INDIRECT = "PII_INDIRECT"
    HEALTH = "HEALTH"
    SYSTEM_SECRET = "SYSTEM_SECRET"
    CANARY = "CANARY"
    BENIGN = "BENIGN"


class DisclosureDecision(str, Enum):
    ALLOW = "ALLOW"
    MINIMIZE = "MINIMIZE"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class TransformationType(str, Enum):
    REDACT_FULL = "REDACT_FULL"
    REDACT_PARTIAL = "REDACT_PARTIAL"
    SYNTHETIC_REPLACE = "SYNTHETIC_REPLACE"
    TOKENIZE = "TOKENIZE"
    PASSTHROUGH = "PASSTHROUGH"


class BrowserActionType(str, Enum):
    NAVIGATE = "NAVIGATE"
    CLICK = "CLICK"
    TYPE = "TYPE"
    SCROLL = "SCROLL"
    EXTRACT = "EXTRACT"
    SUBMIT = "SUBMIT"
    WAIT = "WAIT"


class ActionRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalState(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    TIMEOUT = "TIMEOUT"


class TaskStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"


class BenchmarkPolicy(str, Enum):
    UNPROTECTED_BASELINE = "UNPROTECTED_BASELINE"
    BASIC_REDACTION = "BASIC_REDACTION"
    PRIVACYLENS_TASK_SCOPED = "PRIVACYLENS_TASK_SCOPED"


class DetectedEntity(BaseModel):
    entity_type: SensitivityCategory
    start_idx: Optional[int] = None
    end_idx: Optional[int] = None
    decision: DisclosureDecision = DisclosureDecision.MINIMIZE
    transformation: TransformationType = TransformationType.REDACT_FULL
    replacement: str = "[REDACTED]"
    justification: Optional[str] = None


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    goal: str = Field(..., min_length=1, max_length=500)
    target_domain: str = Field(..., min_length=1, max_length=255)
    allowed_scopes: List[str] = Field(default_factory=list)
    prohibited_scopes: List[str] = Field(default_factory=list)
    ai_provider: Optional[str] = None
    enforce_canary_injection: bool = True


class TaskSession(BaseModel):
    task_id: str
    title: str
    goal: str
    target_domain: str
    allowed_scopes: List[str]
    prohibited_scopes: List[str]
    status: TaskStatus = TaskStatus.INITIALIZED
    created_at: datetime
    updated_at: datetime
    step_count: int = 0
    active_canary_tokens: List[str] = Field(default_factory=list)


class PlanStepRequest(BaseModel):
    task_id: str
    step_index: int
    current_url: str
    sanitized_dom_text: str
    detected_entities: List[DetectedEntity] = Field(default_factory=list)
    canary_tokens_active: List[str] = Field(default_factory=list)
    client_signature: Optional[str] = None


class BrowserAction(BaseModel):
    action_id: str
    type: BrowserActionType
    target_selector: str
    target_description: str
    value: Optional[str] = None
    risk_level: ActionRiskLevel = ActionRiskLevel.LOW
    is_consequential: bool = False
    rationale: str


class PlanStepResponse(BaseModel):
    task_id: str
    step_index: int
    action: Optional[BrowserAction] = None
    approval_state: ApprovalState = ApprovalState.NOT_REQUIRED
    approval_id: Optional[str] = None
    receipt_id: Optional[str] = None
    outbound_inspection_passed: bool = True
    message: Optional[str] = None


class ApprovalDecisionRequest(BaseModel):
    decision: ApprovalState  # APPROVED or REJECTED
    reviewer_comment: Optional[str] = None


class ApprovalItem(BaseModel):
    approval_id: str
    task_id: str
    step_index: int
    proposed_action: BrowserAction
    risk_level: ActionRiskLevel
    reason: str
    status: ApprovalState = ApprovalState.PENDING_APPROVAL
    created_at: datetime
    resolved_at: Optional[datetime] = None
    reviewer_comment: Optional[str] = None


class PrivacyReceipt(BaseModel):
    receipt_id: str
    task_id: str
    step_index: int
    timestamp: datetime
    policy_version: str = "2026.1-task-scoped"
    destination_category: str = "EXTERNAL_AI_ORCHESTRATOR"
    detected_categories: List[str]
    decisions_applied: Dict[str, str]
    transformations_applied: List[str]
    enforcement_outcome: str
    approval_state: ApprovalState
    sanitized_payload_sha256: str
    benchmark_run_id: Optional[str] = None


class BenchmarkTaskSpec(BaseModel):
    task_id: str
    goal: str
    target_domain: str
    allowed_scopes: List[str]
    untrusted_dom: str
    sensitive_entities_present: List[Dict[str, str]]
    planted_canary_tokens: List[str]
    prompt_injection_present: bool = False


class BenchmarkResult(BaseModel):
    run_id: str
    policy: BenchmarkPolicy
    total_tasks: int
    unauthorized_disclosure_rate: float
    detection_precision: float
    detection_recall: float
    legitimate_task_success_rate: float
    false_blocking_rate: float
    unnecessary_sensitive_transmitted_count: int
    useful_context_retained_score: float
    avg_latency_ms: float


class BenchmarkRunResponse(BaseModel):
    run_id: str
    timestamp: datetime
    comparisons: List[BenchmarkResult]
    summary_conclusion: str
