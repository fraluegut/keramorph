"""
Keramorph API – Application settings (pydantic-settings).
"""
from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Loaded from environment / .env file."""

    # app
    app_env: str = "development"
    log_level: str = "INFO"

    # api
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    cors_origins: str = "http://localhost:5173"

    # model
    model_name: str = "keramorph-prod"
    model_type: str = "cnn"
    model_path: str = "models/current"
    model_stage: str = "Production"
    confidence_threshold: float = 0.3

    # mlflow
    mlflow_tracking_uri: str = "http://localhost:5000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
