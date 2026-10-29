from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or .env file.
    No secrets or keys are hardcoded in the codebase.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "PrivacyLens Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS settings
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,chrome-extension://*"

    # AI Provider configuration: "deterministic-mock", "gemini", "openai"
    AI_PROVIDER: str = "deterministic-mock"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Privacy and security enforcement parameters
    STRICT_CANARY_ENFORCEMENT: bool = True
    FAIL_CLOSED_ON_DETECTION_ERROR: bool = True
    MAX_PAYLOAD_SIZE_BYTES: int = 1048576  # 1 MB
    APPROVAL_TIMEOUT_SECONDS: int = 300

    @property
    def origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
