from __future__ import annotations

from typing import Generic, TypeVar

from netframework_core.ddd.domain_event import DomainEvent

TId = TypeVar("TId")


class Entity(Generic[TId]):
    """Identity-compared base: two entities are equal iff same type + id."""

    def __init__(self, id: TId) -> None:
        self.id = id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return type(self) is type(other) and self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))


class AggregateRoot(Entity[TId]):
    """An Entity that is also a consistency boundary and the only thing
    repositories load/save directly. Collects domain events raised by
    business methods; the UnitOfWork drains + publishes them (in-process
    only) after a successful commit."""

    def __init__(self, id: TId) -> None:
        super().__init__(id)
        self._domain_events: list[DomainEvent] = []

    def record_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events, self._domain_events = self._domain_events, []
        return events
