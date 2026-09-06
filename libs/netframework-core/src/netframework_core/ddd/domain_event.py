from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base for a service's *internal* domain events (drained from an
    AggregateRoot after commit, see ddd/unit_of_work.py + ddd/event_bus.py).

    This is NOT what crosses a service boundary — for that, the
    application layer maps a domain event to a plain pydantic contract from
    netframework-contracts and publishes it via netframework_core.eventbus.
    """

    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
