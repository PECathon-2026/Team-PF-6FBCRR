import pytest
from app.models.schemas import (
    SensitivityCategory,
    DisclosureDecision,
    TransformationType,
    ApprovalState,
)


@pytest.mark.asyncio
async def test_full_end_to_end_workflow(client):
    # 1. Create a task session
    task_payload = {
        "title": "Flight Booking Reference Search",
        "goal": "Find the confirmation code for flight booking",
        "target_domain": "fly.example.com",
        "allowed_scopes": ["order_retrieval", "view_receipt"],
        "prohibited_scopes": ["modify_booking", "payment"],
        "ai_provider": "deterministic-mock",
        "enforce_canary_injection": True
    }
    create_resp = await client.post("/api/v1/tasks", json=task_payload)
    assert create_resp.status_code == 201
    task_data = create_resp.json()
    task_id = task_data["task_id"]
    canary_tokens = task_data["active_canary_tokens"]
    assert len(canary_tokens) > 0
    active_canary = canary_tokens[0]

    # 2. Test FAIL-CLOSED when unredacted credit card is in DOM payload
    bad_plan_payload = {
        "task_id": task_id,
        "step_index": 1,
        "current_url": "https://fly.example.com/receipt",
        "sanitized_dom_text": "Booking FLT-123. Unredacted card: 4111 1111 1111 1111",
        "detected_entities": [],
        "canary_tokens_active": [active_canary]
    }
    bad_resp = await client.post(f"/api/v1/tasks/{task_id}/plan", json=bad_plan_payload)
    assert bad_resp.status_code == 422
    err_detail = bad_resp.json()["detail"]
    assert err_detail["error"] == "OUTBOUND_PRIVACY_FIREWALL_VIOLATION"

    # 3. Test FAIL-CLOSED when planted canary secret leaks
    canary_leak_payload = {
        "task_id": task_id,
        "step_index": 1,
        "current_url": "https://fly.example.com/receipt",
        "sanitized_dom_text": f"Booking FLT-123. Hidden token: {active_canary}",
        "detected_entities": [],
        "canary_tokens_active": [active_canary]
    }
    canary_resp = await client.post(f"/api/v1/tasks/{task_id}/plan", json=canary_leak_payload)
    assert canary_resp.status_code == 422
    err_detail = canary_resp.json()["detail"]
    assert err_detail["error"] == "OUTBOUND_PRIVACY_FIREWALL_VIOLATION"

    # 4. Test SUCCESSFUL plan with clean sanitized context
    clean_plan_payload = {
        "task_id": task_id,
        "step_index": 1,
        "current_url": "https://fly.example.com/manage",
        "sanitized_dom_text": "Manage Booking. Card on file: ****-****-****-1111. [View Booking Receipt]",
        "detected_entities": [
            {
                "entity_type": "FINANCIAL",
                "decision": "MINIMIZE",
                "transformation": "REDACT_PARTIAL",
                "replacement": "****-****-****-1111"
            }
        ],
        "canary_tokens_active": [active_canary]
    }
    clean_resp = await client.post(f"/api/v1/tasks/{task_id}/plan", json=clean_plan_payload)
    assert clean_resp.status_code == 200
    plan_data = clean_resp.json()
    assert plan_data["outbound_inspection_passed"] is True
    assert plan_data["receipt_id"] is not None
    receipt_id = plan_data["receipt_id"]

    # 5. Test Consequential Action triggering Human Approval
    consequential_plan_payload = {
        "task_id": task_id,
        "step_index": 2,
        "current_url": "https://fly.example.com/checkout",
        "sanitized_dom_text": "Finalize flight purchase: Total $350. Click Confirm Purchase and Pay Now.",
        "detected_entities": [],
        "canary_tokens_active": [active_canary]
    }
    # To test consequential trigger, create an action with submit or purchase keyword
    # The deterministic mock provider creates high-risk actions when goal includes submit or checkout
    # Let's create a checkout task
    checkout_task_resp = await client.post("/api/v1/tasks", json={
        "title": "Flight Booking Checkout",
        "goal": "Submit flight booking order at checkout",
        "target_domain": "fly.example.com",
        "allowed_scopes": ["order_submission"],
        "prohibited_scopes": [],
        "ai_provider": "deterministic-mock",
        "enforce_canary_injection": True
    })
    checkout_task_id = checkout_task_resp.json()["task_id"]

    checkout_step_resp = await client.post(
        f"/api/v1/tasks/{checkout_task_id}/plan",
        json={
            "task_id": checkout_task_id,
            "step_index": 1,
            "current_url": "https://fly.example.com/checkout",
            "sanitized_dom_text": "Review order. <form id='checkout-form'><button type='submit'>Place Order Now</button></form>",
            "detected_entities": [],
            "canary_tokens_active": []
        }
    )
    assert checkout_step_resp.status_code == 200
    checkout_data = checkout_step_resp.json()
    assert checkout_data["approval_state"] == "PENDING_APPROVAL"
    approval_id = checkout_data["approval_id"]
    assert approval_id is not None

    # 6. List pending approvals
    approvals_resp = await client.get(f"/api/v1/tasks/{checkout_task_id}/approvals")
    assert approvals_resp.status_code == 200
    approvals_list = approvals_resp.json()
    assert len(approvals_list) == 1
    assert approvals_list[0]["approval_id"] == approval_id

    # 7. Human resolves approval
    resolve_resp = await client.post(
        f"/api/v1/tasks/{checkout_task_id}/approvals/{approval_id}",
        json={
            "decision": "APPROVED",
            "reviewer_comment": "Verified order amount; approved to submit."
        }
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "APPROVED"

    # 8. Verify Receipt Integrity
    verify_resp = await client.post(
        "/api/v1/receipts/verify",
        json={
            "receipt_id": receipt_id,
            "payload_to_verify": clean_plan_payload["sanitized_dom_text"]
        }
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verified"] is True

    # 9. Complete Task
    complete_resp = await client.post(f"/api/v1/tasks/{task_id}/complete")
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "COMPLETED"

    # 10. Run Adversarial Benchmark Lab
    bench_resp = await client.post("/api/v1/benchmark/run")
    assert bench_resp.status_code == 200
    bench_data = bench_resp.json()
    assert len(bench_data["comparisons"]) == 3
