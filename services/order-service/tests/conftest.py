from __future__ import annotations

import pytest_asyncio
from netframework_comms.http_adapter import create_http_app
from netframework_core.ddd.event_bus import DomainEventBus
from netframework_core.eventbus.local_bus import LocalEventBus
from netframework_core.persistence.database import create_all_tables, create_engine, create_session_factory

from order_service.application.services import OrderApplicationService
from order_service.interfaces.rest import create_router


@pytest_asyncio.fixture
async def integration_events() -> LocalEventBus:
    """A LocalEventBus instead of Redis — tests assert on what order-service
    *tries* to publish without needing a running Redis instance."""
    return LocalEventBus()


@pytest_asyncio.fixture
async def app(tmp_path, integration_events):
    db_url = f"sqlite+aiosqlite:///{(tmp_path / 'test.db').as_posix()}"
    engine = create_engine(db_url)
    session_factory = create_session_factory(engine)
    await create_all_tables(engine)

    service = OrderApplicationService(session_factory, DomainEventBus(), integration_events)

    http_app = create_http_app("order-service-test")
    http_app.include_router(create_router(service))
    return http_app
