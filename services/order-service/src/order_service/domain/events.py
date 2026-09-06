from __future__ import annotations

from dataclasses import dataclass

from netframework_core.ddd.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class OrderCreated(DomainEvent):
    """Internal domain event — same-service only. See application/services.py
    for where this gets translated into the netframework-contracts
    OrderCreatedEvent that actually crosses the wire to other services."""

    order_id: str
    total_cents: int
