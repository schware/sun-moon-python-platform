"""Cross-service integration-event bus contract. A "topic" is a plain
string both sides agree on (e.g. "order.created"); the message shape is a
pydantic model from netframework-contracts, never a service's internal
domain type — that's what lets the publisher and subscriber be built,
deployed, and versioned independently.
"""
from __future__ import annotations

from typing import Awaitable, Callable, Protocol

from pydantic import BaseModel

Handler = Callable[[BaseModel], Awaitable[None]]


class EventBus(Protocol):
    async def publish(self, topic: str, message: BaseModel) -> None: ...

    def subscribe(self, topic: str, model: type[BaseModel], handler: Handler) -> None: ...

    async def start(self) -> None:
        """Begin dispatching to subscribed handlers (no-op if nothing subscribed)."""
        ...

    async def stop(self) -> None: ...
