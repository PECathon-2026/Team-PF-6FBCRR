"""Data contracts and schemas for PrivacyLens."""
from enum import Enum
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field

class SensitiveCategory(str, Enum):
    AADHAAR = "AADHAAR"
    PAN = "PAN"
    CREDIT_CARD = "CREDIT_CARD"
    CVV = "CVV"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    OTP = "OTP"
    PASSWORD = "PASSWORD"
    API_KEY = "API_KEY"
    JWT = "JWT"
    PRIVATE_KEY = "PRIVATE_KEY"
    IP_ADDRESS = "IP_ADDRESS"
    NAME = "NAME"
    ADDRESS = "ADDRESS"
    PRIVATE_MESSAGE = "PRIVATE_MESSAGE"
    FACE = "FACE"
    SENSITIVE_REGION = "SENSITIVE_REGION"

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class SensitiveSpan(BaseModel):
    category: SensitiveCategory
    text: Optional[str] = None  # None for visual/bounding-box only spans
    start: Optional[int] = None
    end: Optional[int] = None
    bbox: Optional[BoundingBox] = None
    confidence: float = 1.0
    detector: str
    reason: str
    replacement_token: str
    element_id: Optional[str] = None

class DOMElement(BaseModel):
    id: str
    tag: str
    role: Optional[str] = None
    type: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None
    text: str = ""
    value: str = ""
    placeholder: Optional[str] = None
    is_interactive: bool = False
    is_sensitive: bool = False
    bbox: Optional[BoundingBox] = None
    attributes: Dict[str, str] = Field(default_factory=dict)

class RawObservation(BaseModel):
    """Raw observation stored ONLY in trusted local memory, never sent to AI."""
    run_id: str
    page_url: str
    page_origin: str
    page_title: str
    elements: List[DOMElement]
    screenshot_bytes: Optional[bytes] = None
    timestamp: float

class SanitizedElement(BaseModel):
    id: str
    role: Optional[str] = None
    label: Optional[str] = None
    sanitized_text: str = ""
    is_interactive: bool = True
    bbox: Optional[BoundingBox] = None

class SanitizedObservation(BaseModel):
    """Allowlisted safe observation schema sent to the AI egress gateway."""
    run_id: str
    page_origin: str
    page_title: str
    elements: List[SanitizedElement]
    redactions_summary: Dict[str, int] = Field(default_factory=dict)
    sanitized_screenshot_token: Optional[str] = None
    provenance_hash: str  # Locally signed in-memory provenance hash

class ActionType(str, Enum):
    CLICK = "click"
    TYPE_PLACEHOLDER = "type_placeholder"
    FILL_FROM_VAULT = "fill_from_vault"
    SELECT = "select"
    SCROLL = "scroll"
    NAVIGATE = "navigate"
    WAIT = "wait"
    FINISH = "finish"

class ActionProposal(BaseModel):
    action_type: ActionType
    element_id: Optional[str] = None
    value: Optional[str] = None
    secret_alias: Optional[str] = None
    target_url: Optional[str] = None
    reason: str = ""

class RiskLevel(str, Enum):
    SAFE = "SAFE"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ApprovalRequest(BaseModel):
    id: str
    run_id: str
    action: ActionProposal
    target_origin: str
    risk_level: RiskLevel
    reason: str
    consequences: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float

class AuditEventType(str, Enum):
    SESSION_START = "SESSION_START"
    OBSERVATION_COLLECTED = "OBSERVATION_COLLECTED"
    PII_DETECTED = "PII_DETECTED"
    SCREENSHOT_SANITIZED = "SCREENSHOT_SANITIZED"
    GATEWAY_INSPECTED = "GATEWAY_INSPECTED"
    GATEWAY_BLOCKED = "GATEWAY_BLOCKED"
    ACTION_PROPOSED = "ACTION_PROPOSED"
    ACTION_APPROVAL_REQUIRED = "ACTION_APPROVAL_REQUIRED"
    ACTION_APPROVED = "ACTION_APPROVED"
    ACTION_REJECTED = "ACTION_REJECTED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    VAULT_INJECTED = "VAULT_INJECTED"
    SESSION_COMPLETE = "SESSION_COMPLETE"
    SESSION_ERROR = "SESSION_ERROR"

class AuditEvent(BaseModel):
    id: str
    timestamp: float
    event_type: AuditEventType
    run_id: str
    details: Dict[str, Any] = Field(default_factory=dict)
