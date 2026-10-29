# PrivacyLens — Shared API Contract & Schemas

**Version:** 1.0.0  
**Status:** Canonical & Approved  
**Owners:** Agent 1 (Backend Lead) with Agents 2, 3, 4

---

## 1. Core Enumerations & Types

### 1.1 Sensitivity Category
```typescript
type SensitivityCategory =
  | "CREDENTIAL"      // Passwords, bearer tokens, API keys, private keys
  | "FINANCIAL"       // Credit card numbers, CVVs, bank account/routing numbers
  | "PII_DIRECT"      // Full names, SSNs, national ID, passport numbers
  | "PII_INDIRECT"    // Email addresses, phone numbers, postal addresses, IP
  | "HEALTH"          // Medical record numbers, health conditions, prescriptions
  | "SYSTEM_SECRET"   // Session cookies, internal hostnames, environment secrets
  | "CANARY"          // Synthetic canary tokens for leakage measurement
  | "BENIGN";         // Non-sensitive operational data
```

### 1.2 Task-Scoped Disclosure Decision
```typescript
type DisclosureDecision =
  | "ALLOW"     // Data item is strictly necessary for user-authorized task scope
  | "MINIMIZE"  // Data item is partially necessary; mask/truncate/generalize
  | "REVIEW"    // Ambiguous necessity; pause for human confirmation
  | "BLOCK";    // Forbidden, unnecessary, or unapproved disclosure (Fail-closed)
```

### 1.3 Transformation Type
```typescript
type TransformationType =
  | "REDACT_FULL"        // Replaced with categorical placeholder [REDACTED_SSN]
  | "REDACT_PARTIAL"     // Masked keeping structure (e.g. ****-****-****-1234)
  | "SYNTHETIC_REPLACE"  // Replaced with realistic dummy data for format preservation
  | "TOKENIZE"           // Reversible ephemeral surrogate maintained locally only
  | "PASSTHROUGH";       // Transmitted unaltered under active ALLOW policy
```

### 1.4 Browser Action Type & Risk Level
```typescript
type BrowserActionType =
  | "NAVIGATE"   // Open a target URL
  | "CLICK"      // Click DOM element (button, link, checkbox)
  | "TYPE"       // Fill text into input/textarea
  | "SCROLL"     // Adjust viewport
  | "EXTRACT"    // Read text/data from DOM element
  | "SUBMIT"     // Form submission
  | "WAIT";      // Wait for network/DOM condition

type ActionRiskLevel =
  | "LOW"        // Read-only, benign navigation within origin
  | "MEDIUM"     // Filling non-sensitive form fields, pagination
  | "HIGH"       // Form submission, financial/checkout actions, messaging
  | "CRITICAL";  // Password changes, deletions, account management, OAuth grants
```

### 1.5 Approval State
```typescript
type ApprovalState =
  | "NOT_REQUIRED"       // Action risk is LOW/MEDIUM and allowed by policy
  | "PENDING_APPROVAL"   // Action risk is HIGH/CRITICAL; waiting for user sign-off
  | "APPROVED"           // Explicitly authorized by human
  | "REJECTED"           // Explicitly declined by human
  | "TIMEOUT";           // Approval expired without user decision
```

---

## 2. Shared Data Models

### 2.1 Task Context & Creation Request
```json
{
  "title": "Flight Booking Reference Search",
  "goal": "Retrieve the booking confirmation code from my airline receipt",
  "target_domain": "airline.example.com",
  "allowed_scopes": ["order_retrieval", "view_receipt"],
  "prohibited_scopes": ["modify_booking", "payment", "delete_account"],
  "ai_provider": "deterministic-mock",
  "enforce_canary_injection": true
}
```

### 2.2 Inbound Plan Step Request (`POST /api/v1/tasks/{task_id}/plan`)
```json
{
  "task_id": "tsk_01J9XYZ890ABCDEF",
  "step_index": 1,
  "current_url": "https://airline.example.com/manage-booking",
  "sanitized_dom_text": "Booking Reference: [ORDER_ID_PERMITTED]. Card on file: [REDACTED_FINANCIAL]. Password: [REDACTED_CREDENTIAL].",
  "detected_entities": [
    {
      "entity_type": "FINANCIAL",
      "original_length": 16,
      "decision": "MINIMIZE",
      "transformation": "REDACT_PARTIAL",
      "replacement": "****-****-****-4321"
    },
    {
      "entity_type": "CREDENTIAL",
      "original_length": 12,
      "decision": "BLOCK",
      "transformation": "REDACT_FULL",
      "replacement": "[REDACTED_CREDENTIAL]"
    }
  ],
  "canary_tokens_active": ["CANARY-SEC-9842"],
  "client_signature": "sha256-signed-local-digest"
}
```

### 2.3 Proposed Browser Action Response
```json
{
  "task_id": "tsk_01J9XYZ890ABCDEF",
  "step_index": 1,
  "action": {
    "action_id": "act_01J9XYZ",
    "type": "CLICK",
    "target_selector": "button#view-receipt",
    "target_description": "Click 'View Receipt' button",
    "value": null,
    "risk_level": "LOW",
    "is_consequential": false,
    "rationale": "Navigating to receipt view required to extract booking confirmation"
  },
  "approval_state": "NOT_REQUIRED",
  "receipt_id": "rcpt_01J9ABC123",
  "outbound_inspection_passed": true
}
```

### 2.4 Privacy Receipt Schema
```json
{
  "receipt_id": "rcpt_01J9ABC123",
  "task_id": "tsk_01J9XYZ890ABCDEF",
  "step_index": 1,
  "timestamp": "2026-10-30T00:30:00Z",
  "policy_version": "2026.1-task-scoped",
  "destination_category": "EXTERNAL_AI_ORCHESTRATOR",
  "detected_categories": ["FINANCIAL", "CREDENTIAL"],
  "decisions_applied": {
    "FINANCIAL": "MINIMIZE",
    "CREDENTIAL": "BLOCK"
  },
  "transformations_applied": ["REDACT_PARTIAL", "REDACT_FULL"],
  "enforcement_outcome": "SAFE_TRANSMISSION",
  "approval_state": "NOT_REQUIRED",
  "sanitized_payload_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "benchmark_run_id": null
}
```

---

## 3. REST API Endpoint Specification

### System Endpoints
- `GET /api/v1/health`: Basic liveness check. Returns status `healthy`.
- `GET /api/v1/ready`: Readiness check confirming policy engine and AI provider availability.

### Task Management Endpoints
- `POST /api/v1/tasks`: Initialize a new scoped task session.
- `GET /api/v1/tasks/{task_id}`: Fetch task details, state, and timeline.
- `POST /api/v1/tasks/{task_id}/plan`: Orchestrate next step. Applies Outbound Privacy Firewall, AI generation, and Action Validation.
- `POST /api/v1/tasks/{task_id}/complete`: Finalize task session.

### Approval Endpoints
- `GET /api/v1/tasks/{task_id}/approvals`: Retrieve active pending human approvals.
- `POST /api/v1/tasks/{task_id}/approvals/{approval_id}`: Submit human decision (`APPROVED` or `REJECTED`).

### Privacy Receipts & Audit
- `GET /api/v1/tasks/{task_id}/receipts`: Fetch all receipts minted for a task.
- `GET /api/v1/receipts/{receipt_id}`: Retrieve a specific tamper-evident receipt.

### Privacy Policy Lab & Adversarial Benchmark
- `POST /api/v1/benchmark/run`: Execute comparative evaluation across 3 policies:
  1. `UNPROTECTED_BASELINE`: No redaction or minimization.
  2. `BASIC_REDACTION`: Naive regex entity substitution without task context.
  3. `PRIVACYLENS_TASK_SCOPED`: Task-aware minimization + outbound firewall + consequential gating.
- `GET /api/v1/benchmark/runs`: List historical benchmark execution summaries.
