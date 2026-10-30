"""PrivacyLens FastAPI Main Application."""
import base64
import os
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import settings, FIXTURES_DIR
from app.models import (
    ActionProposal, ActionType, ApprovalRequest, ApprovalStatus,
    RiskLevel, AuditEventType, SanitizedObservation, SensitiveSpan
)
from app.audit.logger import audit_logger
from app.privacy.detectors.engine import DetectionEngine
from app.privacy.screenshot import ScreenshotSanitizer
from app.privacy.sanitizer import SanitizerPipeline
from app.privacy.validator import EgressGateway, EgressBlockedException
from app.privacy.vault import vault
from app.browser.browser_manager import BrowserManager
from app.browser.dom_collector import DOMCollector
from app.browser.executor import BrowserExecutor
from app.actions.policy import policy_engine
from app.agents.mock_agent import MockAgent
from app.agents.ollama_agent import OllamaAgent
from app.agents.gateway import ModelEgressGateway

app = FastAPI(
    title="PrivacyLens Core API",
    description="Privacy-Preserving AI Browser Agent Core Orchestrator",
    version="0.1.0"
)

# Enable CORS for local Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator components
detector_engine = DetectionEngine()
screenshot_sanitizer = ScreenshotSanitizer()
sanitizer_pipeline = SanitizerPipeline(detector_engine, screenshot_sanitizer)
egress_gateway = EgressGateway(detector_engine, screenshot_sanitizer)
model_gateway = ModelEgressGateway(egress_gateway)

browser_manager = BrowserManager(browser_type=settings.browser_type, headless=settings.headless)
dom_collector = DOMCollector()
browser_executor = BrowserExecutor()

# Active sessions store: session_id -> SessionState
class SessionState(BaseModel):
    id: str
    task_prompt: str
    target_url: str
    status: str = "active"  # "active", "waiting_approval", "finished", "error"
    step_count: int = 0
    history: List[ActionProposal] = Field(default_factory=list)
    last_action: Optional[ActionProposal] = None
    last_sanitized_obs: Optional[SanitizedObservation] = None
    created_at: float = Field(default_factory=time.time)

active_sessions: Dict[str, SessionState] = {}

# -------------------------------------------------------------
# 1. Health & Status
# -------------------------------------------------------------
@app.get("/api/health")
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "privacylens-core-api",
        "ai_mode": settings.ai_mode,
        "browser_type": settings.browser_type,
        "strict_privacy": settings.strict_privacy,
        "timestamp": time.time(),
    }

# -------------------------------------------------------------
# 2. Synthetic Test Fixtures Serving
# -------------------------------------------------------------
@app.get("/fixtures/{filename}")
def serve_fixture(filename: str):
    file_path = FIXTURES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Fixture {filename} not found")
    return FileResponse(file_path, media_type="text/html")

# -------------------------------------------------------------
# 3. Session Management
# -------------------------------------------------------------
class CreateSessionRequest(BaseModel):
    task_prompt: str
    target_url: str
    ai_mode: Optional[str] = None

@app.post("/api/sessions")
async def create_session(req: CreateSessionRequest):
    session_id = f"sess_{str(uuid.uuid4())[:8]}"
    state = SessionState(
        id=session_id,
        task_prompt=req.task_prompt,
        target_url=req.target_url,
    )
    active_sessions[session_id] = state
    
    # Launch page and navigate
    page = await browser_manager.get_page()
    await page.goto(req.target_url, wait_until="domcontentloaded")
    
    audit_logger.log(
        AuditEventType.SESSION_START,
        session_id,
        {"task": req.task_prompt, "target_url": req.target_url}
    )
    
    return {"session_id": session_id, "status": "active", "target_url": req.target_url}

@app.get("/api/sessions")
def list_sessions():
    return list(active_sessions.values())

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    pending_approvals = policy_engine.get_pending_approvals(session_id)
    return {
        "session": session,
        "pending_approvals": pending_approvals,
    }

# -------------------------------------------------------------
# 4. Agent Execution Step
# -------------------------------------------------------------
@app.post("/api/sessions/{session_id}/step")
async def step_session(session_id: str):
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "waiting_approval":
        raise HTTPException(status_code=400, detail="Action pending user approval. Please approve or reject first.")

    page = await browser_manager.get_page()

    # Step 1: Collect raw observation locally
    t0 = time.time()
    raw_obs = await dom_collector.collect_observation(page, session_id)
    t_collect = time.time() - t0

    # Step 2: Sanitize observation (DOM redaction + irreversible solid pixel masks)
    t0 = time.time()
    sanitized_obs, spans, _ = sanitizer_pipeline.sanitize(raw_obs)
    t_sanitize = time.time() - t0
    session.last_sanitized_obs = sanitized_obs

    # Step 3: Select AI agent based on configuration
    if settings.ai_mode == "local":
        agent = OllamaAgent()
    else:
        agent = MockAgent()

    # Step 4: Propose action through the single egress gateway
    t0 = time.time()
    try:
        _, proposal, _ = await model_gateway.execute_model_step(
            agent=agent,
            task=session.task_prompt,
            observation=sanitized_obs,
            history=session.history
        )
    except EgressBlockedException as err:
        session.status = "error"
        raise HTTPException(status_code=403, detail=f"AI Egress Blocked: {err.reason}")
    t_model = time.time() - t0

    # Step 5: Action policy and risk evaluation
    target_el = next((el for el in sanitized_obs.elements if el.id == proposal.element_id), None)
    el_text = target_el.sanitized_text if target_el else ""
    el_label = target_el.label or "" if target_el else ""

    risk_level, reason, consequences = policy_engine.assess_risk(
        action=proposal,
        element_text=el_text,
        element_label=el_label,
        page_origin=sanitized_obs.page_origin
    )

    if risk_level == RiskLevel.HIGH:
        # Halt execution and create approval request
        appr_req = policy_engine.create_approval_request(
            run_id=session_id,
            action=proposal,
            risk_level=risk_level,
            reason=reason,
            consequences=consequences,
            target_origin=sanitized_obs.page_origin
        )
        session.status = "waiting_approval"
        audit_logger.log(
            AuditEventType.ACTION_APPROVAL_REQUIRED,
            session_id,
            {"approval_id": appr_req.id, "reason": reason}
        )
        return {
            "status": "waiting_approval",
            "approval_request": appr_req,
            "proposed_action": proposal,
            "metrics": {"t_collect": t_collect, "t_sanitize": t_sanitize, "t_model": t_model}
        }

    # Step 6: Safe action: execute directly on browser page
    t0 = time.time()
    success, exec_msg = await browser_executor.execute_action(page, proposal)
    t_exec = time.time() - t0

    session.history.append(proposal)
    session.last_action = proposal
    session.step_count += 1

    if proposal.action_type == ActionType.FINISH:
        session.status = "finished"
        audit_logger.log(AuditEventType.SESSION_COMPLETE, session_id, {"reason": proposal.reason})

    return {
        "status": session.status,
        "action": proposal,
        "execution_message": exec_msg,
        "elements_count": len(sanitized_obs.elements),
        "redactions_count": sum(sanitized_obs.redactions_summary.values()),
        "metrics": {
            "t_collect_ms": round(t_collect * 1000, 2),
            "t_sanitize_ms": round(t_sanitize * 1000, 2),
            "t_model_ms": round(t_model * 1000, 2),
            "t_exec_ms": round(t_exec * 1000, 2),
        }
    }

# -------------------------------------------------------------
# 5. Human Approval Flow
# -------------------------------------------------------------
class ApprovalDecisionRequest(BaseModel):
    decision: str  # "approve" or "reject"

@app.post("/api/sessions/{session_id}/approve/{approval_id}")
async def decide_approval(session_id: str, approval_id: str, req: ApprovalDecisionRequest):
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    appr = policy_engine.get_approval(approval_id)
    if not appr or appr.run_id != session_id:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if req.decision == "approve":
        policy_engine.update_approval_status(approval_id, ApprovalStatus.APPROVED)
        audit_logger.log(AuditEventType.ACTION_APPROVED, session_id, {"approval_id": approval_id})
        
        # Execute approved action
        page = await browser_manager.get_page()
        success, exec_msg = await browser_executor.execute_action(page, appr.action)
        
        session.history.append(appr.action)
        session.last_action = appr.action
        session.step_count += 1
        session.status = "active"

        return {"status": "approved", "execution_message": exec_msg}
    else:
        policy_engine.update_approval_status(approval_id, ApprovalStatus.REJECTED)
        audit_logger.log(AuditEventType.ACTION_REJECTED, session_id, {"approval_id": approval_id})
        session.status = "active"
        return {"status": "rejected", "message": "Action was rejected by user"}

# -------------------------------------------------------------
# 6. Local Privacy Preview (Before/After)
# -------------------------------------------------------------
@app.get("/api/privacy/preview/{session_id}")
def get_privacy_preview(session_id: str, response: Response):
    # Strict cache control: NEVER cache sensitive previews
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"

    preview_data = sanitizer_pipeline.get_local_preview(session_id)
    if not preview_data:
        raise HTTPException(status_code=404, detail="No preview available for session")

    raw_b64 = base64.b64encode(preview_data["raw_bytes"]).decode("utf-8") if preview_data.get("raw_bytes") else None
    san_b64 = base64.b64encode(preview_data["sanitized_bytes"]).decode("utf-8") if preview_data.get("sanitized_bytes") else None
    
    spans: List[SensitiveSpan] = preview_data.get("spans", [])

    return {
        "session_id": session_id,
        "is_local_only": True,
        "raw_screenshot": f"data:image/png;base64,{raw_b64}" if raw_b64 else None,
        "sanitized_screenshot": f"data:image/png;base64,{san_b64}" if san_b64 else None,
        "spans": [
            {
                "category": s.category.value,
                "replacement_token": s.replacement_token,
                "confidence": s.confidence,
                "detector": s.detector,
                "reason": s.reason,
                "bbox": s.bbox.model_dump() if s.bbox else None,
            }
            for s in spans
        ],
        "created_at": preview_data.get("created_at"),
    }

# -------------------------------------------------------------
# 7. Vault Management
# -------------------------------------------------------------
@app.get("/api/vault")
def list_vault_aliases():
    return {"aliases": vault.list_aliases()}

class AddVaultSecretRequest(BaseModel):
    alias: str
    value: str

@app.post("/api/vault")
def add_vault_secret(req: AddVaultSecretRequest):
    vault.register_secret(req.alias, req.value)
    return {"status": "registered", "alias": req.alias}

# -------------------------------------------------------------
# 8. Audit Log
# -------------------------------------------------------------
@app.get("/api/audit")
def get_audit_logs(run_id: Optional[str] = None):
    return audit_logger.get_events(run_id)

# -------------------------------------------------------------
# 9. Automated Evaluation Runner
# -------------------------------------------------------------
@app.get("/api/evaluation/latest")
def get_latest_evaluation():
    import json
    report_path = Path(__file__).resolve().parent.parent.parent / "reports" / "results.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="No evaluation results found. Run evaluation first.")
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/evaluate")
async def run_evaluation_endpoint():
    from scripts.evaluate import run_full_evaluation
    results = await run_full_evaluation()
    return results
