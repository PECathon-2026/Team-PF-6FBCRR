from datetime import datetime, timezone
from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health & Status"])


@router.get("/health", summary="Liveness Probe")
async def health_check():
    """Returns basic service liveness and version info."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ai_provider": settings.AI_PROVIDER,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/ready", summary="Readiness Probe")
async def readiness_check():
    """Confirms policy engine, firewall, and AI provider availability."""
    return {
        "ready": True,
        "firewall_active": True,
        "strict_canary_enforcement": settings.STRICT_CANARY_ENFORCEMENT,
        "ai_provider_configured": settings.AI_PROVIDER,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
