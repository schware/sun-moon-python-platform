"""Application layer: orchestrates domain + persistence per use case, and is
where the internal/external event boundary is crossed explicitly.

`create_order` does two distinct things once `uow.commit()` succeeds:
  1. (mechanism, already ran inside the UnitOfWork) any same-service
     listener got the internal `OrderCreated` domain event via DomainEventBus.
  2. (explicit, here) translate that same fact into the netframework-contracts
     `OrderCreatedEvent` and publish it on the integration-event bus — this
     is the only thing another service (ai-agent-service) ever sees.
"""
from __future__ import annotations

from datetime import datetime, timezone

from netframework_contracts.order_events import ORDER_CREATED_TOPIC, OrderCreatedEvent
from netframework_core.ddd.event_bus import DomainEventBus
from netframework_core.ddd.unit_of_work import SqlAlchemyUnitOfWork
from netframework_core.eventbus.base import EventBus
from netframework_core.exceptions import NotFoundError
from sqlalchemy.ext.asyncio import async_sessionmaker

from order_service.application.dto import CreateOrderRequest, OrderLineDTO, OrderResponse
from order_service.domain.entities import Order, OrderLine
from order_service.infrastructure.repository_impl import SqlAlchemyOrderRepository


class OrderApplicationService:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        domain_event_bus: DomainEventBus,
        integration_events: EventBus,
    ) -> None:
        self._session_factory = session_factory
        self._domain_event_bus = domain_event_bus
        self._integration_events = integration_events

    async def create_order(self, request: CreateOrderRequest) -> OrderResponse:
        lines = [OrderLine(**line.model_dump()) for line in request.lines]
        order = Order.create(lines)

        async with SqlAlchemyUnitOfWork(self._session_factory, self._domain_event_bus) as uow:
            await SqlAlchemyOrderRepository(uow.session).add(order)
            uow.collect_events_from(order)
            await uow.commit()

        await self._integration_events.publish(
            ORDER_CREATED_TOPIC,
            OrderCreatedEvent(
                order_id=order.id,
                total_cents=order.total_cents,
                occurred_at=datetime.now(timezone.utc),
            ),
        )
        return self._to_response(order)

    async def get_order(self, order_id: str) -> OrderResponse:
        async with SqlAlchemyUnitOfWork(self._session_factory, self._domain_event_bus) as uow:
            order = await SqlAlchemyOrderRepository(uow.session).get(order_id)
        if order is None:
            raise NotFoundError(f"order {order_id} not found")
        return self._to_response(order)

    async def list_orders(self) -> list[OrderResponse]:
        async with SqlAlchemyUnitOfWork(self._session_factory, self._domain_event_bus) as uow:
            orders = await SqlAlchemyOrderRepository(uow.session).list()
        return [self._to_response(order) for order in orders]

    @staticmethod
    def _to_response(order: Order) -> OrderResponse:
        return OrderResponse(
            id=order.id,
            status=order.status.value,
            total_cents=order.total_cents,
            lines=[
                OrderLineDTO(sku=l.sku, quantity=l.quantity, unit_price_cents=l.unit_price_cents)
                for l in order.lines
            ],
        )
