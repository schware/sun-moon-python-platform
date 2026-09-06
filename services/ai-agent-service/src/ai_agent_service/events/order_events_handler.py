"""Subscribes to order-service's OrderCreated integration event. This file
is the entire "AI Agent reacts to what happened in Order" seam — it depends
only on netframework-contracts (the wire shape) and the generic EventBus
protocol, never on order-service's code or database.
"""
from __future__ import annotations

from netframework_contracts.order_events import ORDER_CREATED_TOPIC, OrderCreatedEvent
from netframework_core.eventbus.base import EventBus
from netframework_core.logging import get_logger

from ai_agent_service.application.assistant_service import AssistantService

logger = get_logger(__name__)


def register_order_event_handlers(bus: EventBus, assistant: AssistantService) -> None:
    async def on_order_created(event: OrderCreatedEvent) -> None:
        note = await assistant.ask(
            f"A new order {event.order_id} totalling {event.total_cents} cents was just "
            "created. Give a one-line operational note about it."
        )
        logger.info("ai_agent_order_note", order_id=event.order_id, note=note)

    bus.subscribe(ORDER_CREATED_TOPIC, OrderCreatedEvent, on_order_created)
