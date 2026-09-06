#!/usr/bin/env python3
"""ai-agent-service entrypoint. Run with:

    uv run --package ai-agent-service python -m ai_agent_service.main

Boots its own HTTP endpoint (/assistant/ask) and, separately, a Redis
subscription to order-service's integration events — the two are
independent: the REST endpoint works even if Redis is down, it just won't
get proactive order notes.
"""
from __future__ import annotations

import asyncio

import uvicorn
from dotenv import load_dotenv
from netframework_comms.http_adapter import create_http_app
from netframework_core.eventbus.redis_bus import create_redis_bus
from netframework_core.logging import configure_logging, get_logger

from ai_agent_service.application.assistant_service import AssistantService
from ai_agent_service.application.order_client import OrderServiceClient
from ai_agent_service.config import AiAgentServiceConfig
from ai_agent_service.events.order_events_handler import register_order_event_handlers
from ai_agent_service.interfaces.rest import create_router

logger = get_logger(__name__)


async def main() -> None:
    load_dotenv()
    config = AiAgentServiceConfig()
    configure_logging(config.log_level, service_name=config.service_name)

    order_client = OrderServiceClient(config.order_service_base_url)
    assistant = AssistantService(
        provider=config.ai_provider,
        model=config.ai_model,
        api_key=config.ai_api_key,
        max_iterations=config.ai_max_tool_iterations,
        order_client=order_client,
    )

    integration_events = create_redis_bus(config.redis_url)
    register_order_event_handlers(integration_events, assistant)
    await integration_events.start()

    http_app = create_http_app(config.service_name)
    http_app.include_router(create_router(assistant))

    logger.info(
        "ai_agent_service_ready",
        http_port=config.http_port,
        ai_provider=config.ai_provider,
        order_service=config.order_service_base_url,
    )

    uv_config = uvicorn.Config(http_app, host=config.http_host, port=config.http_port, log_level="info")
    try:
        await uvicorn.Server(uv_config).serve()
    finally:
        await integration_events.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
