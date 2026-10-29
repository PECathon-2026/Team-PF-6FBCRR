from app.services.outbound_firewall import outbound_firewall


def test_firewall_blocks_luhn_valid_credit_card():
    # Valid Visa test number
    payload = "Here is the user order. Card number: 4111 1111 1111 1111. Please proceed."
    result = outbound_firewall.inspect_payload(payload)
    assert result.passed is False
    assert len(result.violations) > 0
    assert any(v.category == "FINANCIAL_CARD_EXFILTRATION" for v in result.violations)


def test_firewall_blocks_ssn():
    payload = "User details: Name John, SSN 123-45-6789."
    result = outbound_firewall.inspect_payload(payload)
    assert result.passed is False
    assert any(v.category == "DIRECT_PII_EXFILTRATION" for v in result.violations)


def test_firewall_blocks_active_canary_token():
    canary = "CANARY-SEC-9988-ALERT"
    payload = f"Extracted page content with token: {canary} and some text."
    result = outbound_firewall.inspect_payload(payload, active_canary_tokens=[canary])
    assert result.passed is False
    assert any(v.category == "CANARY_LEAKAGE" for v in result.violations)


def test_firewall_blocks_api_key():
    payload = "Configuration: sk-live998811223344556677889900."
    result = outbound_firewall.inspect_payload(payload)
    assert result.passed is False
    assert any(v.category == "CREDENTIAL_EXFILTRATION" for v in result.violations)


def test_firewall_passes_clean_sanitized_payload():
    payload = "Flight booking confirmed for Order #FLT-9872. Total: $450.00. Seat 14B."
    result = outbound_firewall.inspect_payload(
        payload,
        active_canary_tokens=["CANARY-DIFFERENT-TOKEN"]
    )
    assert result.passed is True
    assert len(result.violations) == 0
    assert result.sha256_digest is not None
