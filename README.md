# 🛡️ PrivacyLens — Autonomous Privacy-Preserving AI Browser Agent

[![PECathon 2026](https://img.shields.io/badge/PECathon_2026-PS--004-blue.svg?style=for-the-badge&logo=target)](https://github.com/PECathon-2026/Team-PF-6FBCRR)
[![Team](https://img.shields.io/badge/Team-PF--6FBCRR-emerald.svg?style=for-the-badge)](https://github.com/PECathon-2026/Team-PF-6FBCRR)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg?style=for-the-badge&logo=next.js)](https://nextjs.org)
[![Camoufox](https://img.shields.io/badge/Browser-Camoufox_Stealth-orange.svg?style=for-the-badge)](https://camoufox.com)
[![Detection Recall](https://img.shields.io/badge/Detection_Recall-100%25-brightgreen.svg?style=for-the-badge)]()
[![Leak Rate](https://img.shields.io/badge/Leak_Rate-0.0%25-success.svg?style=for-the-badge)]()

> **A local-first, fail-closed privacy architecture and autonomous browser agent that enforces task-scoped information minimization, real-time multimodal sanitization, human-in-the-loop approval gates, and cryptographic audit trails for AI-driven web tasks.**

---

## 📌 Problem Statement & Core Hypothesis

### **PECathon 2026 — Problem Statement PS-004**
> Traditional privacy tools blindly redact initial prompts or rely entirely on cloud-side alignment. In complex autonomous web tasks, sensitive PII, authentication tokens, financial credentials, and session secrets continuously leak through dynamic DOM changes and screenshot observations.
>
> **The PrivacyLens Engineering Hypothesis:**  
> *A privacy system must enforce task-scoped disclosure boundaries dynamically throughout an autonomous task lifecycle, actively measure information necessity, redact multimodal inputs locally before egress, pause on consequential operations, and verify zero outbound leakage with mathematical and empirical guarantees.*

---

## 🚀 Key Features & Capabilities

- 🔒 **Local-First Multimodal Sanitization Pipeline:**
  - **DOM Redaction:** Local tree-traversal stripping hidden credentials, sensitive attributes, and tokens before AI exposure.
  - **Irreversible Pixel Masking:** Solid bounding-box pixel obfuscation on screenshots so visual models cannot bypass text filters.
- 🎯 **Algorithmic & Contextual Detectors:**
  - **Aadhaar Engine:** 12-digit Indian national identity detection validated using the **Verhoeff algorithm**.
  - **Credit / Debit Cards:** Card number detection validated using the **Luhn algorithm**.
  - **PAN & Government IDs:** Format-strict regex and checksum-aware validators.
  - **Credentials & High-Entropy Secrets:** Passwords, API tokens, JWTs, OAuth headers, OTPs, session identifiers.
  - **Contact & PII:** Emails, phone numbers, addresses, and physical coordinates.
- 🛑 **Fail-Closed AI Egress Gateway:**
  - Every candidate payload serialized for AI models (Ollama local LLMs or external providers) passes through a fail-closed validator.
  - Planted honeytokens and canaries trigger instantaneous request aborts (`403 Forbidden`).
- ✋ **Consequential Action Human-in-the-Loop (HITL) Gate:**
  - Actions classified as **HIGH RISK** (e.g., payments, account deletions, password changes, terms submission) automatically suspend execution into `waiting_approval` state until explicit human review.
- 🔑 **Cryptographic Local Vault:**
  - Reversible pseudonymization: sensitive values are mapped to deterministic vault tokens (e.g., `[SECRET_VAULT_ALIAS_1]`) stored strictly in local memory and resolved only during final in-browser execution.
- 📊 **Interactive Next.js Dashboard:**
  - Real-time task runner with step-by-step telemetry, before/after privacy diff inspector, audit event stream, and empirical benchmark visualizations.
- 🦊 **Camoufox Stealth Browser Integration:**
  - Anti-fingerprinting browser automation engine with native ad-blocking and OS fingerprint spoofing.

---

## 🏛️ System Architecture

```
                       ┌──────────────────────────────────────────────┐
                       │          Next.js Real-time Dashboard         │
                       │   (Live Session, Privacy Diff, Benchmark)    │
                       └──────────────────────┬───────────────────────┘
                                              │ HTTP / JSON API
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               PrivacyLens FastAPI Core                                 │
│                                                                                        │
│   ┌────────────────────┐      ┌─────────────────────────┐      ┌───────────────────┐   │
│   │  Browser Manager   │◄────►│  DOM / Vision Collector │─────►│ Sanitizer Pipeline│   │
│   │ (Camoufox Stealth) │      │  (Playwright Collector) │      │ (Pixel + DOM PII) │   │
│   └─────────┬──────────┘      └─────────────────────────┘      └─────────┬─────────┘   │
│             │                                                            │             │
│             │ Action Execution                                           ▼             │
│             │                                                  ┌───────────────────┐   │
│   ┌─────────┴──────────┐                                       │   Egress Gate     │   │
│   │ Browser Executor   │                                       │ (Fail-Closed Zero │   │
│   └─────────▲──────────┘                                       │  Leak Validator)  │   │
│             │                                                  └─────────┬─────────┘   │
│   ┌─────────┴──────────┐      ┌─────────────────────────┐                │             │
│   │ Policy Risk Engine │◄────►│   Human Approval Gate   │                ▼             │
│   │  (Assess Actions)  │      │(Approve / Reject Conseq)│      ┌───────────────────┐   │
│   └────────────────────┘      └─────────────────────────┘      │ AI Reasoning Agent│   │
│                                                                │  (Ollama / Mock)  │   │
│   ┌────────────────────┐      ┌─────────────────────────┐      └───────────────────┘   │
│   │ Local Memory Vault │      │    Audit Log Stream     │                              │
│   └────────────────────┘      └─────────────────────────┘                              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧪 Empirical Benchmark & Evaluation

PrivacyLens includes a built-in repeatable adversarial benchmark harness (`scripts/evaluate.py`) running across 6 diverse synthetic enterprise and e-commerce workflows (`checkout`, `auth`, `support`, `video`, `dev_settings`, `adversarial`).

| Metric | Measured Score | Baseline Unprotected | Goal / Target |
| :--- | :---: | :---: | :---: |
| **Detection Recall** | **100.0%** (1.00) | 0.0% | > 95% |
| **Redaction Precision** | **90.0%** (0.90) | N/A | > 85% |
| **Observed Leak Rate** | **0.0%** (0 leaks) | 100.0% | **0.0% (Fail-Closed)** |
| **Task Success Rate** | **100.0%** (6/6) | 100.0% | 100% |
| **Canary Injection Blocked** | **True** (Passed) | Failed | True |
| **DOM Collection Latency (P50)**| **38.4 ms** | N/A | < 100 ms |
| **Sanitization Latency (P50)** | **27.2 ms** | N/A | < 50 ms |
| **Peak Memory Footprint** | **~103.6 MB** | N/A | < 250 MB |

---

## 🛠️ Quickstart & Running Locally

### Option A: Running with Docker Compose (Recommended)

Run the entire stack (FastAPI Backend + Next.js Dashboard) in a single command:

```bash
docker compose up --build
```

- **Next.js Dashboard:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Core API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

### Option B: Local Development Setup

#### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & npm
- (Optional) [Ollama](https://ollama.ai/) for running local LLMs (`qwen2.5-coder:7b` or `llama3.2`)

#### 1. Backend Setup
```bash
# Navigate to the backend directory
cd apps/api

# Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Install Playwright browser binaries
playwright install firefox

# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Dashboard Setup
```bash
# Open a new terminal and navigate to the dashboard
cd apps/dashboard

# Install npm dependencies
npm install

# Start Next.js development server
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the live dashboard.

---

## ⚙️ Configuration (`.env`)

Copy `.env.example` to `.env` to configure runtime parameters:

```ini
# Server
PORT=8000
HOST=0.0.0.0
DEBUG=false

# Browser Engine
BROWSER_TYPE=camoufox
HEADLESS=true
CAMOUFOX_OS_PROFILE=macos
CAMOUFOX_UBLOCK=true

# AI Egress & Security
LOCAL_ONLY_MODE=true
REQUIRE_APPROVAL_FOR_HIGH_RISK=true

# Local LLM Integration (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# Dashboard URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🔌 API Reference & Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | System health, browser status, and privacy configuration |
| `POST` | `/api/sessions` | Create a new scoped browser session with a task prompt |
| `GET` | `/api/sessions` | List all active agent sessions |
| `GET` | `/api/sessions/{id}` | Get session status, current step count, and pending approvals |
| `POST` | `/api/sessions/{id}/step` | Execute an autonomous reasoning and browser execution step |
| `POST` | `/api/sessions/{id}/approve/{appr_id}` | Approve or reject a consequential high-risk browser action |
| `GET` | `/api/privacy/preview/{id}` | Inspect raw vs. sanitized screenshots & detected PII spans |
| `GET` | `/api/vault` | List registered tokenized vault aliases |
| `POST` | `/api/vault` | Register a new sensitive credential into local memory vault |
| `GET` | `/api/audit` | Query immutable audit events log |
| `GET` | `/api/evaluation/latest` | Retrieve latest benchmark scorecards and latency distributions |
| `POST` | `/api/evaluate` | Trigger full automated adversarial evaluation suite |

---

## 🔬 Running the Evaluation Benchmark

Run the automated evaluation benchmark suite:

```bash
python scripts/evaluate.py
```

This will run all 6 benchmark scenarios, measure precision, recall, and latencies, and output:
- `reports/results.json`
- `reports/results.csv`

---

## 📂 Repository Layout

```
.
├── apps/
│   ├── api/                     # FastAPI Core Orchestrator
│   │   ├── app/
│   │   │   ├── actions/         # Policy Engine & Risk Classification
│   │   │   ├── agents/          # Mock & Ollama Local AI Agents
│   │   │   ├── audit/           # Audit Logging & Event Trail
│   │   │   ├── browser/         # Camoufox/Playwright Browser Execution
│   │   │   ├── privacy/         # Detection Engine, Pixel/DOM Sanitizer, Vault
│   │   │   │   └── detectors/   # Aadhaar, Luhn, PAN, Secrets, Contact, etc.
│   │   │   ├── config.py        # Centralized App Configuration
│   │   │   ├── main.py          # REST API & Route Handlers
│   │   │   └── models.py        # Pydantic Schemas & Data Contracts
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── dashboard/               # Next.js 14 Tailwind Dashboard
│       ├── src/
│       │   ├── app/             # App router pages (Session, Privacy, Benchmark, Settings)
│       │   └── lib/api.ts       # Type-safe API client
│       ├── Dockerfile
│       └── package.json
├── docker-compose.yml           # Unified multi-service deployment
├── reports/                     # Benchmark results (CSV & JSON)
├── scripts/
│   └── evaluate.py              # Automated 6-scenario evaluation suite
├── tests/
│   └── fixtures/                # Synthetic adversarial testing web pages
├── .env.example                 # Environment configuration template
└── README.md                    # Project documentation
```

---

## 👥 Team & Governance

- **Competition:** PECathon 2026 (Problem Statement PS-004)
- **Team Code:** Team-PF-6FBCRR
- **Team Lead & Master Engineer:** Paras Kumar Verma ([@parasverma07](https://github.com/parasverma07))
- **Repository:** [https://github.com/PECathon-2026/Team-PF-6FBCRR](https://github.com/PECathon-2026/Team-PF-6FBCRR)

---

## 📄 License

This project is licensed under the **MIT License**.
