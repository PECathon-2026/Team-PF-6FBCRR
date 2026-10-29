# PrivacyLens — System Architecture Specification

## 1. Executive Summary & Core Hypothesis

PrivacyLens is a browser-first, modular, local-first privacy-preserving AI assistance system developed for PECathon 2026 (Problem Statement PS-004).

### Core Engineering Hypothesis
> **A privacy system should enforce the user's disclosure rules throughout an AI task, not merely redact the initial prompt. It should check what information is necessary for the task, where information is going, and whether each proposed disclosure is authorized. It should then measure whether the task remains useful.**

PrivacyLens treats this as an empirical engineering hypothesis to evaluate systematically—not a speculative assertion. The system couples local-first sensitive data minimization with task-scoped disclosure governance, an outbound privacy firewall, independent browser-action validation, verifiable privacy receipts, and an adversarial benchmark suite.

---

## 2. High-Level Component Architecture

PrivacyLens is structured as four decoupled modules with clean network and RPC contracts:

```
+-----------------------------------------------------------------------------------+
|                              USER BROWSER / HOST                                  |
|                                                                                   |
|  +---------------------------------+    +--------------------------------------+  |
|  |       Agent 2: Frontend         |    |    Agent 4: Browser Security Agent   |  |
|  | - React 19 + TypeScript + Vite  |    | - Manifest V3 Background Worker      |  |
|  | - Task Dashboard & Policy Panel |    | - Untrusted DOM Capture / CDP        |  |
|  | - Approval & Receipt Inspector  |    | - Constrained Action Dispatcher      |  |
|  | - Policy Lab Benchmark UI       |    | - Pre-action DOM State Verifier      |  |
|  +----------------+----------------+    +------------------+-------------------+  |
|                   |                                        |                      |
|                   +-------------------+--------------------+                      |
|                                       | (Internal Chrome Message Bus / Port)      |
|                                       v                                           |
|                         +-----------------------------+                           |
|                         |  Agent 3: Privacy Engine    |                           |
|                         | - Local PII/Secret Detector |                           |
|                         | - Task-Scoped Minimization  |                           |
|                         | - Screenshot OCR & Masker   |                           |
|                         | - Canary Token Generator    |                           |
|                         +--------------+--------------+                           |
+----------------------------------------|------------------------------------------+
                                         | HTTP / WebSocket
                                         v (Strictly Sanitized Outbound Boundary)
+-----------------------------------------------------------------------------------+
|                        Agent 1: PrivacyLens Backend (FastAPI)                     |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | 1. Ingestion Gate & Task Session Manager                                    |  |
|  |    - Validates task scope, session tokens, and client schema                |  |
|  +-------------------------------------+---------------------------------------+  |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  | 2. Task-Scoped Disclosure Policy Engine (Deterministic Rules)               |  |
|  |    - Evaluates: [Scope, Data Sensitivity, Purpose, Destination, Policy]     |  |
|  |    - Decisions: ALLOW | MINIMIZE | REVIEW | BLOCK (Fail-Closed)              |  |
|  +-------------------------------------+---------------------------------------+  |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  | 3. Final Outbound Serialization & Privacy Firewall Gate                     |  |
|  |    - Deep AST/JSON scan of exact outbound bytes immediately before egress   |  |
|  |    - Blocks unredacted secrets, unexpected PII, canary leaks (Fail-Closed)  |  |
|  +-------------------------------------+---------------------------------------+  |
|                                        v                                          |
|  +-------------------------------------+---------------------------------------+  |
|  | 4. External AI Adapter (Plug-and-Play Orchestrator)                         |  |
|  |    - Deterministic Mock Provider (Zero-credential, deterministic testing)   |  |
|  |    - Cloud LLM Provider (Gemini 2.5 / OpenAI / Anthropic via Env Keys)      |  |
|  |    - Strictly receives sanitized payload; zero raw access                   |  |
|  +-------------------------------------+---------------------------------------+  |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  | 5. Independent Action Validator & Security Policy Guard                     |  |
|  |    - Validates AI response against browser action schema                    |  |
|  |    - Enforces Action Risk Classification (LOW, MEDIUM, HIGH, CRITICAL)      |  |
|  |    - Manages Approval State Machine (Requires Human Confirmation)           |  |
|  |    - Defends against indirect prompt injection embedded in DOM content      |  |
|  +-------------------------------------+---------------------------------------+  |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  | 6. Privacy Receipts & Audit Service                                         |  |
|  |    - Generates cryptographic receipt (SHA-256 payload digest)               |  |
|  |    - Zero raw secrets or PII stored in logs or receipts                     |  |
|  |    - Non-repudiable audit ledger for user inspection                        |  |
|  +-------------------------------------+---------------------------------------+  |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  | 7. Privacy Policy Lab & Adversarial Benchmark Engine                        |  |
|  |    - Multi-mode comparative evaluation (Unprotected vs Basic vs PrivacyLens)|  |
|  |    - Automated metrics: Leakage %, Detection P/R, Utility %, Latency        |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 3. Data Flow & Boundary Enforcement

### 3.1 End-to-End Workflow Sequence
1. **User Goal Ingestion:** The user specifies a high-level browsing goal (e.g., "Find the order number for my flight booking on travel.example.com").
2. **Context Capture (Agent 4):** Browser extension captures current page DOM snapshot and relevant viewport coordinates.
3. **Local Privacy Analysis (Agent 3):**
   - The Privacy Engine scans the DOM text, attributes, and user prompt locally in the browser/host.
   - Detects PII (names, emails, phones, SSNs, credit cards), credentials (passwords, auth tokens, API keys), and canary secrets.
   - Applies task-scoped minimization (e.g., masking credit card digits and passwords while preserving order IDs required for the task).
4. **Backend Ingestion (Agent 1):** The sanitized DOM context and task parameters arrive at the backend `/api/v1/tasks/{task_id}/plan` endpoint.
5. **Final Outbound Firewall Check (Agent 1):**
   - The backend runs a secondary, independent outbound validation pass over the exact serialized JSON payload.
   - If any unmasked high-sensitivity patterns or active canary tokens are detected, the request is **blocked immediately (Fail-Closed)**.
6. **AI Planning (Agent 1):**
   - The sanitized payload is transmitted to the configured AI Adapter (or Deterministic Mock Provider).
   - AI outputs structured candidate actions (e.g., `CLICK`, `TYPE`, `NAVIGATE`, `EXTRACT`).
7. **Independent Action Validation (Agent 1):**
   - The backend verifies that the proposed action matches safe action schemas.
   - Risk rating is computed based on action type, target element, and destination domain.
   - If consequential (e.g., form submit, payment, deletion, message dispatch), approval state transitions to `PENDING_APPROVAL`.
8. **User Approval (Agent 2):**
   - Frontend prompts the user with clear context, proposed target, and minimized data to be entered.
   - User reviews and confirms (`APPROVED` or `REJECTED`).
9. **Execution (Agent 4):**
   - Browser agent executes the approved action via Chrome Debugging Protocol (CDP) / WebDriver.
   - Action result status is recorded.
10. **Receipt Generation (Agent 1):**
    - A tamper-evident Privacy Receipt is minted containing policy version, destination, detected categories, action taken, and SHA-256 digest of sanitized payload.

---

## 4. Security & Privacy Invariants

| ID | Invariant | Enforcement Mechanism |
|---|---|---|
| **INV-1** | No Raw Secret Egress | Final outbound payload inspection fails closed before network dispatch. |
| **INV-2** | No Blind LLM Trust | AI models are never queried to self-certify privacy safety; deterministic rules govern policy. |
| **INV-3** | Consequential Approval | Consequential actions (submits, payments, data modifications) require explicit user sign-off. |
| **INV-4** | Untrusted Page Content | Webpage content is treated as adversarial; instructions in DOM cannot override hard privacy policy. |
| **INV-5** | Secret-Free Receipts | Receipts log cryptographic digests, timestamps, and redaction counts; never raw values or reversible mappings. |
| **INV-6** | Deterministic Fallback | When external credentials are unavailable, deterministic mock mode runs transparently without network leaks. |

---

## 5. Technology Stack Summary

| Subsystem | Technology | Justification |
|---|---|---|
| **Backend** | Python 3.13, FastAPI, Pydantic v2, Uvicorn | High performance, strict typed validation, native async, clear security middleware |
| **Testing** | Pytest, pytest-asyncio, HTTPX | Comprehensive asynchronous unit, integration, and security test coverage |
| **Frontend** | React 19, TypeScript, Vite | Modern, reactive UI for dashboard, approval modal, and benchmark viewer |
| **Browser Extension** | Chrome Extensions Manifest V3 | Standard modern extension platform with isolated content scripts and background service worker |
| **Privacy Engine** | TypeScript / WebAssembly / Regex / AST | Deterministic local detection, zero-latency in-browser sanitization |
