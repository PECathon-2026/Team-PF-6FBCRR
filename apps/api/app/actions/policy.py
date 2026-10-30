"""Action policy validator and risk classification engine."""
import uuid
import time
from typing import Tuple, List, Optional
from app.models import (
    ActionProposal, ActionType, RiskLevel,
    ApprovalRequest, ApprovalStatus
)

HIGH_RISK_TERMS = [
    "pay", "purchase", "place order", "confirm order", "submit order",
    "send message", "send", "submit payment", "delete", "destroy",
    "update password", "transfer"
]

class ActionPolicyEngine:
    def __init__(self, allowed_domains: Optional[List[str]] = None):
        self.allowed_domains = allowed_domains or ["localhost", "127.0.0.1", "securecorp.local"]
        self._approvals: dict[str, ApprovalRequest] = {}

    def assess_risk(
        self,
        action: ActionProposal,
        element_text: str = "",
        element_label: str = "",
        page_origin: str = ""
    ) -> Tuple[RiskLevel, str, str]:
        """
        Assesses action risk level and determines if human approval is required.
        Returns:
            (risk_level: RiskLevel, reason: str, consequences: str)
        """
        combined_text = f"{element_text} {element_label} {action.reason}".lower()

        # 1. Navigation risk
        if action.action_type == ActionType.NAVIGATE and action.target_url:
            is_allowed = any(domain in action.target_url for domain in self.allowed_domains)
            if not is_allowed:
                return (
                    RiskLevel.HIGH,
                    f"External navigation to untrusted domain: {action.target_url}",
                    "May expose session state or navigate to phishing/external origins"
                )

        # 2. Payment / Checkout confirmation risk
        if any(term in combined_text for term in ["purchase", "place order", "confirm order", "pay now", "submit payment"]):
            return (
                RiskLevel.HIGH,
                "Final purchase / payment confirmation action",
                "Will trigger financial transaction and finalize order"
            )

        # 3. Message dispatch / Support chat send
        if action.action_type == ActionType.CLICK and any(term in combined_text for term in ["send", "submit message", "reply"]):
            return (
                RiskLevel.HIGH,
                "Outbound message transmission to support / external recipient",
                "Will send message text to external service or user"
            )

        # 4. Account credential or destructive modification
        if any(term in combined_text for term in ["delete account", "reset password", "change email", "revoke"]):
            return (
                RiskLevel.HIGH,
                "Account modification or destructive change",
                "Modifies security credentials or deletes user data"
            )

        # 5. Safe actions: typing, clicking non-destructive buttons, scrolling, waiting
        return (
            RiskLevel.SAFE,
            "Non-destructive interaction",
            "Safe UI interaction within trusted fixture domain"
        )

    def create_approval_request(
        self,
        run_id: str,
        action: ActionProposal,
        risk_level: RiskLevel,
        reason: str,
        consequences: str,
        target_origin: str
    ) -> ApprovalRequest:
        req_id = f"appr_{str(uuid.uuid4())[:8]}"
        req = ApprovalRequest(
            id=req_id,
            run_id=run_id,
            action=action,
            target_origin=target_origin,
            risk_level=risk_level,
            reason=reason,
            consequences=consequences,
            status=ApprovalStatus.PENDING,
            created_at=time.time(),
        )
        self._approvals[req_id] = req
        return req

    def get_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        return self._approvals.get(approval_id)

    def update_approval_status(self, approval_id: str, status: ApprovalStatus) -> bool:
        if approval_id in self._approvals:
            self._approvals[approval_id].status = status
            return True
        return False

    def get_pending_approvals(self, run_id: Optional[str] = None) -> List[ApprovalRequest]:
        reqs = [r for r in self._approvals.values() if r.status == ApprovalStatus.PENDING]
        if run_id:
            reqs = [r for r in reqs if r.run_id == run_id]
        return reqs

policy_engine = ActionPolicyEngine()
