"""In-memory EventBus — same interface as RedisEventBus, zero infrastructure.
Used by tests and by any service running standalone without Redis; swap for
RedisEventBus (see redis_bus.py) to actually cross a process boundary."""
from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel

from netframework_core.eventbus.base import Handler
from netframework_core.logging import get_logger

logger = get_logger(__name__)


class LocalEventBus:
    def __init__(self) -> None:
        self._subs: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, topic: str, model: type[BaseModel], handler: Handler) -> None:
        self._subs[topic].append(handler)

    async def publish(self, topic: str, message: BaseModel) -> None:
        for handler in self._subs.get(topic, []):
            try:
                await handler(message)
            except Exception as exc:  # noqa: BLE001
                logger.error("integration_event_handler_failed", topic=topic, error=str(exc))

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass
