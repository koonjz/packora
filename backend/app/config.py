"""
Packora application settings.

All configuration is read from environment variables (or .env file).
Feature flags (ENABLE_CV_FEATURE, ENABLE_LLM_EXPLANATION) are defined here
so the rest of the application can import them from one canonical place.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database ---
    database_url: str = (
        "postgresql+asyncpg://packora:changeme@localhost:5432/packora_db"
    )

    # --- App ---
    app_env: str = "development"
    secret_key: str = "dev-secret-key-replace-in-production"
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # --- Feature flags ---
    enable_cv_feature: bool = False
    enable_llm_explanation: bool = True

    # --- LLM (optional) ---
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 5

    # --- CV (optional) ---
    cv_model_path: str = "backend/app/cv/mobilenetv3_packora.pt"
    cv_confidence_threshold: float = 0.70


settings = Settings()
