"""PrivacyLens configuration module."""
import os
from pathlib import Path
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures" / "sites"
ANNOTATIONS_DIR = ROOT_DIR / "tests" / "fixtures" / "annotations"
REPORTS_DIR = ROOT_DIR / "reports"

class Settings(BaseModel):
    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=8000)
    ai_mode: str = Field(default="local")  # "mock", "local" (Ollama), "cloud"
    enable_cloud_ai: bool = Field(default=False)
    cloud_api_key: str = Field(default="")
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.2")
    strict_privacy: bool = Field(default=True)
    audit_retention_hours: int = Field(default=24)
    browser_type: str = Field(default="camoufox")  # "camoufox", "firefox", "chromium"
    headless: bool = Field(default=True)
    fixtures_url: str = Field(default="http://127.0.0.1:8000/fixtures")
    canary_seed: str = Field(default="PL_CANARY_")

    @classmethod
    def load(cls) -> "Settings":
        return cls(
            api_host=os.getenv("API_HOST", "127.0.0.1"),
            api_port=int(os.getenv("API_PORT", "8000")),
            ai_mode=os.getenv("AI_MODE", "mock"),
            enable_cloud_ai=os.getenv("ENABLE_CLOUD_AI", "false").lower() == "true",
            cloud_api_key=os.getenv("CLOUD_API_KEY", ""),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            strict_privacy=os.getenv("STRICT_PRIVACY", "true").lower() == "true",
            audit_retention_hours=int(os.getenv("AUDIT_RETENTION_HOURS", "24")),
            browser_type=os.getenv("BROWSER_TYPE", "camoufox"),
            headless=os.getenv("HEADLESS", "true").lower() == "true",
            fixtures_url=os.getenv("FIXTURES_URL", "http://127.0.0.1:8000/fixtures"),
            canary_seed=os.getenv("CANARY_SEED", "PL_CANARY_"),
        )

settings = Settings.load()
