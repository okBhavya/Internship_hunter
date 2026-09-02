"""Application configuration using pydantic-settings."""
from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Internship Hunter"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "dev-secret-key-change-in-production"

    # Database
    database_url: str = f"sqlite:///{BASE_DIR / 'internship_hunter.db'}"

    # AI / LLM
    gemini_api_key: str = ""
    openai_api_key: str = ""
    ai_provider: str = "local"

    # Browser
    headless_browser: bool = True
    browser_timeout: int = 30000

    # Job sources
    remotive_api_key: str = ""
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""

    # Scheduling
    discovery_schedule_hour: int = 8
    discovery_schedule_minute: int = 0
    discovery_frequency: str = "daily"

    # Rate limiting
    max_requests_per_minute: int = 30
    request_delay_seconds: float = 2.0

    # Paths
    uploads_dir: str = str(BASE_DIR / "uploads")
    resumes_dir: str = str(BASE_DIR / "uploads" / "resumes")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
