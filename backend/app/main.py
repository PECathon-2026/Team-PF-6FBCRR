from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.routes import health, tasks, approvals, receipts, benchmark


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure services ready
    yield
    # Shutdown


app = FastAPI(
    title="PrivacyLens Backend",
    version=settings.APP_VERSION,
    description=(
        "Browser-First Privacy-Preserving AI Assistance Engine (PECathon 2026, Problem Statement PS-004). "
        "Provides local-first sensitive data minimization, task-scoped disclosure decisions, "
        "fail-closed outbound privacy firewall, independent action validation, verifiable privacy receipts, "
        "and a repeatable adversarial benchmark lab."
    ),
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_and_payload_limit(request: Request, call_next):
    # Enforce maximum payload size limit
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_PAYLOAD_SIZE_BYTES:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "Payload exceeds maximum allowed size."}
        )

    response = await call_next(request)

    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Include API Routers under /api/v1
app.include_router(health.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(approvals.router, prefix="/api/v1")
app.include_router(receipts.router, prefix="/api/v1")
app.include_router(benchmark.router, prefix="/api/v1")

# Also include health probes at root for standard platform container checks
app.include_router(health.router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "api_v1": "/api/v1"
    }
