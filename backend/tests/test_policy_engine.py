from datetime import datetime, timezone
from app.models.schemas import (
    SensitivityCategory,
    DisclosureDecision,
    TransformationType,
    TaskSession,
    TaskStatus,
)
from app.services.policy_engine import policy_engine


def create_test_session(allowed_scopes, prohibited_scopes=None):
    return TaskSession(
        task_id="tsk_test_policy_01",
        title="Test Task Session",
        goal="Search flight booking",
        target_domain="fly.example.com",
        allowed_scopes=allowed_scopes,
        prohibited_scopes=prohibited_scopes or [],
        status=TaskStatus.IN_PROGRESS,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        active_canary_tokens=["CANARY-TEST-1234"]
    )


def test_canary_always_blocked():
    session = create_test_session(allowed_scopes=["everything"])
    decision, trans, repl, just = policy_engine.evaluate_disclosure(
        session,
        SensitivityCategory.CANARY,
        "CANARY-TEST-1234"
    )
    assert decision == DisclosureDecision.BLOCK
    assert trans == TransformationType.REDACT_FULL
    assert repl == "[BLOCKED_CANARY_SECRET]"


def test_credential_always_blocked():
    session = create_test_session(allowed_scopes=["user_profile"])
    decision, trans, repl, just = policy_engine.evaluate_disclosure(
        session,
        SensitivityCategory.CREDENTIAL,
        "SuperSecretPassword!"
    )
    assert decision == DisclosureDecision.BLOCK
    assert trans == TransformationType.REDACT_FULL
    assert "[REDACTED_CREDENTIAL]" in repl


def test_financial_minimized_when_scope_authorized():
    session = create_test_session(allowed_scopes=["checkout", "payment"])
    decision, trans, repl, just = policy_engine.evaluate_disclosure(
        session,
        SensitivityCategory.FINANCIAL,
        "4111 2222 3333 4321"
    )
    assert decision == DisclosureDecision.MINIMIZE
    assert trans == TransformationType.REDACT_PARTIAL
    assert repl == "****-****-****-4321"


def test_financial_blocked_when_scope_unauthorized():
    session = create_test_session(allowed_scopes=["read_news"])
    decision, trans, repl, just = policy_engine.evaluate_disclosure(
        session,
        SensitivityCategory.FINANCIAL,
        "4111 2222 3333 4321"
    )
    assert decision == DisclosureDecision.BLOCK
    assert trans == TransformationType.REDACT_FULL
    assert repl == "[REDACTED_FINANCIAL]"


def test_pii_email_minimized_when_scope_authorized():
    session = create_test_session(allowed_scopes=["order_retrieval"])
    decision, trans, repl, just = policy_engine.evaluate_disclosure(
        session,
        SensitivityCategory.PII_INDIRECT,
        "john.doe@company.org"
    )
    assert decision == DisclosureDecision.MINIMIZE
    assert trans == TransformationType.REDACT_PARTIAL
    assert repl == "j***@company.org"


def test_benign_data_allowed():
    session = create_test_session(allowed_scopes=["read_news"])
    decision, trans, repl, just = policy_engine.evaluate_disclosure(
        session,
        SensitivityCategory.BENIGN,
        "Flight schedule confirmed for tomorrow 9 AM"
    )
    assert decision == DisclosureDecision.ALLOW
    assert trans == TransformationType.PASSTHROUGH
    assert repl == "Flight schedule confirmed for tomorrow 9 AM"
