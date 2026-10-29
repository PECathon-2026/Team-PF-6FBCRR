# PrivacyLens — Codebase Ownership & Team Governance

## 1. Principles of Division
To eliminate merge conflicts, avoid duplicative implementations, and preserve independent agency across sessions:
1. **Module Isolation:** Each agent owns an exclusive directory tree.
2. **Contract-First Development:** Agents integrate exclusively through the shared schemas defined in `docs/API_CONTRACT.md`.
3. **No Direct Overwrites:** No agent may unilaterally rewrite another agent's production module. If schema changes are required, update `docs/API_CONTRACT.md` and document the decision in `ACTIVITY.md`.
4. **Independent Branches:** Each agent works on their dedicated feature branch:
   - Agent 1: `feature/master-backend`
   - Agent 2: `feature/frontend`
   - Agent 3: `feature/privacy-engine`
   - Agent 4: `feature/browser-security`

---

## 2. Ownership Matrix

| Agent | Role | Dedicated Directory | Primary Responsibilities |
|---|---|---|---|
| **Agent 1** (Master Engineer / Backend Lead) | Architecture, Backend, Shared Contracts, Integration | `backend/`<br>`docs/`<br>`ACTIVITY.md`<br>`README.md` | - FastAPI application & configuration<br>- Outbound payload inspection firewall<br>- AI provider abstraction & mock adapter<br>- Action risk evaluation & approval state machine<br>- Privacy receipt generation & audit ledger<br>- Adversarial benchmark orchestration<br>- End-to-end integration verification |
| **Agent 2** (Frontend Specialist) | UI / UX Developer | `frontend/` | - React 19 + TypeScript + Vite app<br>- Extension Popup & Side Panel interface<br>- Live task monitoring & step visualizer<br>- Human-in-the-loop Approval Modal<br>- Privacy Receipts Inspector<br>- Privacy Policy Lab interactive dashboard |
| **Agent 3** (Privacy Engine Specialist) | Detection, Sanitization, Canary Engine | `privacy-engine/` | - Local client-side PII & secret detection<br>- Task-scoped disclosure minimization logic<br>- Screenshot OCR & bounding-box redaction<br>- Synthetic canary token generation<br>- Local AST & DOM attribute sanitizer |
| **Agent 4** (Browser Security Specialist) | Browser Extension, Automation, CDP | `browser-security/` | - Chrome Extension Manifest V3 scaffolding<br>- Background service worker & Content Scripts<br>- Safe DOM snapshot extraction<br>- Constrained browser action runner (CDP/WebDriver)<br>- Pre-action DOM verification<br>- Untrusted web input isolation |

---

## 3. Boundary & Communication Protocol

```
[Agent 4: Browser Extension]
           |
           v (Local DOM & Viewport)
[Agent 3: Privacy Engine (Client-side)]
           |
           v (Sanitized Context + Redaction Manifest)
[Agent 1: Backend Gateway & Outbound Firewall] <---> [Agent 2: Frontend UI]
           |                                                 |
           v (Outbound Sanitized Payload only)               v (Approval Decisions)
[External AI / Mock Provider]                       [Human Reviewer]
```

- **Frontend <-> Backend:** Standard JSON over REST & WebSockets adhering to `docs/API_CONTRACT.md`.
- **Extension <-> Privacy Engine:** High-speed in-memory / WebWorker message passing.
- **Backend <-> External AI:** Outbound Firewall intercepts and strictly validates payload before egress.
