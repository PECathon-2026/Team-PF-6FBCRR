# PrivacyLens — Privacy-Preserving AI Browser Agent

> PECathon 2026 — Problem Statement PS-004

PrivacyLens is an advanced AI browser agent designed with local-first privacy guarantees, an outbound privacy firewall, independent action validation, and a verifiable Privacy Proof Engine.

## Project Structure
- `backend/`: FastAPI backend orchestration, AI provider abstraction, and action validator (Agent 1).
- `frontend/`: Extension popup UI and task dashboard in React, TypeScript, and Vite (Agent 2).
- `privacy-engine/`: Local detection, redaction, OCR masking, and outbound firewall (Agent 3).
- `browser-security/`: Manifest V3 extension, CDP automation, and security testing (Agent 4).
- `docs/`: System architecture, API contracts, and ownership specifications.
