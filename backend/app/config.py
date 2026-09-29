"""
Packora application settings.

All configuration is read from environment variables (or .env file).
Feature flags (ENABLE_CV_FEATURE, ENABLE_LLM_EXPLANATION) are defined here
so the rest of the application can import them from one canonical place.
"""
from __future__ import annotations

import json
from typing import Any
from pydantic import field_validator
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
    allowed_origins: list[str] | str = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return ["*"]
            if v == "*":
                return ["*"]
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed]
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

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

