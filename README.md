# PrivacyLens — Browser-First Privacy-Preserving AI Assistant

> **PECathon 2026 — Problem Statement PS-004**  
> **Team:** Team-PF-6FBCRR  
> **Lead / Master Engineer:** Paras Kumar Verma (`parasverma07`)

---

## 1. System Overview

PrivacyLens is an extensible, browser-first, local-first privacy-preserving AI assistance system designed for autonomous and semi-autonomous web workflows.

### Core Engineering Hypothesis
> **A privacy system should enforce the user's disclosure rules throughout an AI task, not merely redact the initial prompt. It should check what information is necessary for the task, where information is going, and whether each proposed disclosure is authorized. It should then measure whether the task remains useful.**

PrivacyLens implements and experimentally evaluates this hypothesis through:
- **Local-First Detection & Task-Scoped Minimization:** Scans untrusted DOM text and attributes locally before data egress.
- **Task-Scoped Disclosure Decisions:** Evaluates information necessity against user-authorized task boundaries (`ALLOW`, `MINIMIZE`, `REVIEW`, `BLOCK`).
- **Fail-Closed Outbound Privacy Firewall:** Intercepts and deeply inspects exact serialized payloads immediately before external AI transmission. Rejects unmasked credentials, PII, or planted canary secrets.
- **Independent Browser Action Validator:** Classifies action risk (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) and enforces mandatory human approval for consequential operations (form submission, payments, account changes).
- **Cryptographic Privacy Receipts:** Generates verifiable receipts with SHA-256 payload digests without persisting raw secrets or unredacted PII.
- **Privacy Policy Lab & Adversarial Benchmark:** A repeatable evaluation harness comparing Unprotected Baselines, Basic Redaction, and PrivacyLens Task-Scoped Enforcement.

---

## 2. Repository Layout & Agent Ownership

```
├── backend/            # Agent 1 (Backend Lead): FastAPI, Policy Engine, Outbound Firewall, AI Orchestrator
├── frontend/           # Agent 2 (Frontend Specialist): React 19, TypeScript, Vite, Extension Popup & UI
├── privacy-engine/     # Agent 3 (Privacy Specialist): Client-side PII detector, Masking, Canary engine
├── browser-security/   # Agent 4 (Browser Specialist): Manifest V3 extension, CDP runner, Security testing
├── docs/               # System specifications
│   ├── ARCHITECTURE.md # Architectural design, data flow, sequence diagrams
│   ├── API_CONTRACT.md # Shared schemas, types, REST & WebSocket endpoints
│   ├── OWNERSHIP.md    # Multi-agent ownership matrix & governance
│   └── THREAT_MODEL.md # Threat analysis, attack vectors, defense matrix
├── ACTIVITY.md         # Multi-agent coordination and status ledger
└── README.md           # Quickstart and overview
```

---

## 3. Quickstart & Installation

### Prerequisites
- Python 3.13+
- Node.js 22+ & npm 10+
- Chrome or Chromium browser

### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running Backend Server
```bash
# Starts FastAPI server on http://localhost:8000
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Automated Test Suite
```bash
cd backend
pytest -v
```

---

## 4. End-to-End Workflow Verification

1. **Create Scoped Task:** `POST /api/v1/tasks` with declared scope (e.g. `order_retrieval`).
2. **Context Minimization & Firewall:** `POST /api/v1/tasks/{task_id}/plan` passes DOM context. Privacy Engine minimizes irrelevant PII; Outbound Firewall verifies zero leakages.
3. **AI Planning:** Configured AI provider (or Deterministic Mock Provider) generates next candidate browser action.
4. **Action Risk & Human Approval:** If action is consequential (`SUBMIT`, payment, deletion), backend pauses in `PENDING_APPROVAL` until approved via `POST /api/v1/tasks/{task_id}/approvals/{approval_id}`.
5. **Receipt Minting:** Cryptographic receipt with SHA-256 digest is generated and retrievable via `GET /api/v1/tasks/{task_id}/receipts`.
6. **Policy Lab Benchmark:** Run `POST /api/v1/benchmark/run` to evaluate leakage rate and task utility across multiple privacy policies.
