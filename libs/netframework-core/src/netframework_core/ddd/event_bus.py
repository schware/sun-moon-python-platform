"""In-process domain event bus — deliberately NOT how services talk to each
other (that's netframework_core.eventbus, over Redis). This is for
listeners living inside the same service/process as the aggregate that
raised the event. Most services will have zero same-service subscribers and
that's fine; the mechanism costs nothing to leave wired up in UnitOfWork.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Awaitable, Callable, TypeVar

from netframework_core.ddd.domain_event import DomainEvent
from netframework_core.logging import get_logger

logger = get_logger(__name__)

E = TypeVar("E", bound=DomainEvent)
Handler = Callable[[DomainEvent], Awaitable[None]]


class DomainEventBus:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: type[E], handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(type(event), [])
        if not handlers:
            return
        results = await asyncio.gather(*(h(event) for h in handlers), return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.error("domain_event_handler_failed", event=type(event).__name__, error=str(result))

    async def publish_all(self, events: list[DomainEvent]) -> None:
        for event in events:
            await self.publish(event)
