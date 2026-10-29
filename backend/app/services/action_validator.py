import re
import uuid
from datetime import datetime, timezone
from typing import Tuple, Optional
from app.models.schemas import (
    BrowserAction,
    BrowserActionType,
    ActionRiskLevel,
    ApprovalState,
    ApprovalItem,
)


class ActionValidator:
    """
    Independent Browser Action Validator and Security Policy Guard.
    Evaluates AI-proposed browser actions independently of the language model.
    Enforces risk classification, detects indirect prompt injection payloads,
    and mandates human approval for consequential operations.
    """

    # High-risk selector or label keywords indicating consequential operations
    CONSEQUENTIAL_KEYWORDS = {
        "pay", "purchase", "buy", "checkout", "place order", "confirm order",
        "submit", "transfer", "send money", "wire", "delete", "destroy",
        "remove account", "change password", "reset password", "revoke",
        "grant access", "authorise", "authorize", "approve payment"
    }

    # Malicious injection markers that must never be permitted in action targets or values
    DANGEROUS_PATTERNS = [
        re.compile(r"javascript\s*:", re.IGNORECASE),
        re.compile(r"data\s*:\s*text\/html", re.IGNORECASE),
        re.compile(r"<\s*script\b", re.IGNORECASE),
        re.compile(r"document\.cookie", re.IGNORECASE),
        re.compile(r"localStorage\.", re.IGNORECASE),
        re.compile(r"window\.location", re.IGNORECASE),
    ]

    def validate_and_classify(
        self,
        task_id: str,
        step_index: int,
        action: BrowserAction
    ) -> Tuple[BrowserAction, ApprovalState, Optional[ApprovalItem]]:
        """
        Validates the proposed browser action against security invariants.
        Returns:
            (sanitized_action, approval_state, optional_approval_item)
        """
        # Invariant 1: Reject any arbitrary code execution attempts
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(action.target_selector) or (action.value and pattern.search(action.value)):
                # Block malicious script injection, downgrade to safe WAIT
                action.type = BrowserActionType.WAIT
                action.target_selector = "body"
                action.value = None
                action.risk_level = ActionRiskLevel.CRITICAL
                action.rationale = "SECURITY INTERVENTION: Malicious script injection pattern detected and neutralized."
                action.is_consequential = True

                approval_item = ApprovalItem(
                    approval_id=f"appr_{uuid.uuid4().hex[:12]}",
                    task_id=task_id,
                    step_index=step_index,
                    proposed_action=action,
                    risk_level=ActionRiskLevel.CRITICAL,
                    reason="Potential script injection attempt neutralized; requires manual confirmation to resume.",
                    status=ApprovalState.PENDING_APPROVAL,
                    created_at=datetime.now(timezone.utc),
                )
                return action, ApprovalState.PENDING_APPROVAL, approval_item

        # Invariant 2: Classify Risk Level & Consequential Nature
        is_consequential = False
        risk_level = ActionRiskLevel.LOW
        reasons = []

        # Form submissions are inherently consequential
        if action.type == BrowserActionType.SUBMIT:
            is_consequential = True
            risk_level = ActionRiskLevel.HIGH
            reasons.append("Form submission carries irreversible external state changes.")

        # Inspect target description and selector for consequential keywords
        text_to_scan = f"{action.target_description} {action.target_selector}".lower()
        matched_keywords = [kw for kw in self.CONSEQUENTIAL_KEYWORDS if kw in text_to_scan]

        if matched_keywords:
            is_consequential = True
            if any(k in ["delete", "remove account", "change password", "wire", "transfer"] for k in matched_keywords):
                risk_level = ActionRiskLevel.CRITICAL
                reasons.append(f"Operation involves critical action: {', '.join(matched_keywords)}")
            else:
                risk_level = ActionRiskLevel.HIGH
                reasons.append(f"Operation matches consequential keyword: {', '.join(matched_keywords)}")

        # Password or credential input
        if action.type == BrowserActionType.TYPE and "password" in action.target_selector.lower():
            is_consequential = True
            risk_level = ActionRiskLevel.HIGH
            reasons.append("Typing into password input field requires explicit user authorization.")

        # Update action attributes
        action.risk_level = risk_level
        action.is_consequential = is_consequential

        # Invariant 3: Consequential actions mandate human-in-the-loop approval
        if is_consequential or risk_level in (ActionRiskLevel.HIGH, ActionRiskLevel.CRITICAL):
            approval_item = ApprovalItem(
                approval_id=f"appr_{uuid.uuid4().hex[:12]}",
                task_id=task_id,
                step_index=step_index,
                proposed_action=action,
                risk_level=risk_level,
                reason="; ".join(reasons) or "Consequential action requires explicit human confirmation.",
                status=ApprovalState.PENDING_APPROVAL,
                created_at=datetime.now(timezone.utc),
            )
            return action, ApprovalState.PENDING_APPROVAL, approval_item

        return action, ApprovalState.NOT_REQUIRED, None


action_validator = ActionValidator()
