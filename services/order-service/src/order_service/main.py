#!/usr/bin/env python3
"""order-service entrypoint. Run with:

    uv run --package order-service python -m order_service.main

Boots its own HTTP (REST) and TCP listeners, its own SQLite database, and
connects to Redis only to *publish* integration events — this service has
no subscriptions of its own, so it never calls RedisEventBus.start().
"""
from __future__ import annotations

import asyncio

import uvicorn
from dotenv import load_dotenv
from netframework_comms.http_adapter import create_http_app
from netframework_comms.tcp_adapter import start_tcp_server
from netframework_core.ddd.event_bus import DomainEventBus
from netframework_core.eventbus.redis_bus import create_redis_bus
from netframework_core.logging import configure_logging, get_logger
from netframework_core.persistence.database import create_all_tables, create_engine, create_session_factory

from order_service.application.services import OrderApplicationService
from order_service.config import OrderServiceConfig
from order_service.interfaces.rest import create_router
from order_service.interfaces.tcp import create_tcp_handlers

logger = get_logger(__name__)


async def main() -> None:
    load_dotenv()
    config = OrderServiceConfig()
    configure_logging(config.log_level, service_name=config.service_name)

    engine = create_engine(config.database_url, echo=config.database_echo)
    session_factory = create_session_factory(engine)
    await create_all_tables(engine)

    domain_events = DomainEventBus()
    integration_events = create_redis_bus(config.redis_url)

    service = OrderApplicationService(session_factory, domain_events, integration_events)

    http_app = create_http_app(config.service_name)
    http_app.include_router(create_router(service))

    if config.tcp_enabled:
        await start_tcp_server(config.tcp_host, config.tcp_port, create_tcp_handlers(service))

    logger.info("order_service_ready", http_port=config.http_port, tcp_enabled=config.tcp_enabled)

    uv_config = uvicorn.Config(http_app, host=config.http_host, port=config.http_port, log_level="info")
    await uvicorn.Server(uv_config).serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
