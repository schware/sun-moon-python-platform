"""Unit of Work: one transaction boundary. Domain events collected on
aggregates during the transaction are published to the (in-process)
DomainEventBus only *after* commit succeeds, so a rolled-back change never
leaks an event to same-service listeners. Publishing an *integration* event
to other services is a separate, explicit step the application layer takes
after `commit()` returns — see order-service's application/services.py.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from netframework_core.ddd.domain_event import DomainEvent
from netframework_core.ddd.entity import AggregateRoot
from netframework_core.ddd.event_bus import DomainEventBus


class AbstractUnitOfWork(ABC):
    async def __aenter__(self) -> "AbstractUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            await self.rollback()

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...

    @abstractmethod
    def collect_events_from(self, *aggregates: AggregateRoot) -> None: ...


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    session: AsyncSession

    def __init__(self, session_factory: async_sessionmaker, event_bus: DomainEventBus) -> None:
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._pending_events: list[DomainEvent] = []

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await super().__aexit__(exc_type, exc, tb)
        await self.session.close()

    def collect_events_from(self, *aggregates: AggregateRoot) -> None:
        for aggregate in aggregates:
            self._pending_events.extend(aggregate.pull_events())

    async def commit(self) -> None:
        await self.session.commit()
        events, self._pending_events = self._pending_events, []
        await self._event_bus.publish_all(events)

    async def rollback(self) -> None:
        await self.session.rollback()
        self._pending_events.clear()
