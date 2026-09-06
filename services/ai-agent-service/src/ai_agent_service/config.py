from __future__ import annotations

import os

from netframework_core.config import BaseServiceConfig


class AiAgentServiceConfig(BaseServiceConfig):
    service_name: str = "ai-agent-service"
    http_port: int = 8082

    ai_provider: str = "echo"
    ai_model: str = "claude-sonnet-5"
    ai_api_key_env: str = "ANTHROPIC_API_KEY"
    ai_max_tool_iterations: int = 4

    # This is the only thing that couples the two services: a config value,
    # not an import. Point it at order-service's public REST API.
    order_service_base_url: str = "http://localhost:8081"

    @property
    def ai_api_key(self) -> str | None:
        return os.environ.get(self.ai_api_key_env)
