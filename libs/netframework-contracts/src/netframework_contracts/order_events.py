from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

ORDER_CREATED_TOPIC = "order.created"


class OrderCreatedEvent(BaseModel):
    """Integration event published by order-service, consumed by
    ai-agent-service (and any future subscriber). Deliberately thinner than
    order-service's internal Order aggregate — only what other services
    actually need to know."""

    order_id: str
    total_cents: int
    occurred_at: datetime
