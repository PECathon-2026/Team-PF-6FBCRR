from app.models.schemas import (
    BrowserAction,
    BrowserActionType,
    ActionRiskLevel,
    ApprovalState,
)
from app.services.action_validator import action_validator


def test_benign_navigation_not_consequential():
    action = BrowserAction(
        action_id="act_01",
        type=BrowserActionType.CLICK,
        target_selector="a.view-receipt",
        target_description="View booking receipt",
        value=None,
        risk_level=ActionRiskLevel.LOW,
        is_consequential=False,
        rationale="View receipt to extract booking code"
    )
    validated, state, item = action_validator.validate_and_classify("tsk_01", 1, action)
    assert state == ApprovalState.NOT_REQUIRED
    assert validated.risk_level == ActionRiskLevel.LOW
    assert validated.is_consequential is False
    assert item is None


def test_form_submission_triggers_approval():
    action = BrowserAction(
        action_id="act_02",
        type=BrowserActionType.SUBMIT,
        target_selector="form#checkout",
        target_description="Submit finalized order",
        value=None,
        risk_level=ActionRiskLevel.LOW,
        is_consequential=False,
        rationale="Submit order"
    )
    validated, state, item = action_validator.validate_and_classify("tsk_01", 1, action)
    assert state == ApprovalState.PENDING_APPROVAL
    assert validated.risk_level == ActionRiskLevel.HIGH
    assert validated.is_consequential is True
    assert item is not None
    assert item.status == ApprovalState.PENDING_APPROVAL


def test_consequential_keywords_trigger_approval():
    action = BrowserAction(
        action_id="act_03",
        type=BrowserActionType.CLICK,
        target_selector="button#btn-purchase",
        target_description="Confirm Purchase and Pay Now",
        value=None,
        risk_level=ActionRiskLevel.LOW,
        is_consequential=False,
        rationale="Complete purchase"
    )
    validated, state, item = action_validator.validate_and_classify("tsk_01", 1, action)
    assert state == ApprovalState.PENDING_APPROVAL
    assert validated.risk_level in (ActionRiskLevel.HIGH, ActionRiskLevel.CRITICAL)
    assert validated.is_consequential is True
    assert item is not None


def test_script_injection_neutralized():
    action = BrowserAction(
        action_id="act_04",
        type=BrowserActionType.CLICK,
        target_selector="a[href='javascript:stealCookies()']",
        target_description="Click button",
        value=None,
        risk_level=ActionRiskLevel.LOW,
        is_consequential=False,
        rationale="Follow link"
    )
    validated, state, item = action_validator.validate_and_classify("tsk_01", 1, action)
    # Neutralized to WAIT
    assert validated.type == BrowserActionType.WAIT
    assert state == ApprovalState.PENDING_APPROVAL
    assert item is not None
    assert "script injection" in item.reason.lower()
