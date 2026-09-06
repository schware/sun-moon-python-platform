"""Base settings every service extends. 12-factor style: config comes from
environment variables (+ an optional .env file for local dev), not a shared
YAML file — each service is deployed independently (its own container, its
own env), so its config has to travel with it independently too.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "netframework-service"
    env: str = "development"
    log_level: str = "INFO"

    http_host: str = "0.0.0.0"
    http_port: int = 8080

    redis_url: str = "redis://localhost:6379/0"
