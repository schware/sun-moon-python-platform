from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from netframework_core.ddd.entity import AggregateRoot

TAggregate = TypeVar("TAggregate", bound=AggregateRoot)
TId = TypeVar("TId")


class Repository(ABC, Generic[TAggregate, TId]):
    """Domain-facing collection-like interface. Concrete persistence lives
    in a service's infrastructure/ layer, implementing this ABC — the
    application layer depends only on this interface."""

    @abstractmethod
    async def get(self, id: TId) -> TAggregate | None: ...

    @abstractmethod
    async def add(self, aggregate: TAggregate) -> None: ...

    @abstractmethod
    async def list(self, *, limit: int = 100, offset: int = 0) -> list[TAggregate]: ...
