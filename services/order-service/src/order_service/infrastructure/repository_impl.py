from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from order_service.domain.entities import Order, OrderLine, OrderStatus
from order_service.domain.repository import OrderRepository
from order_service.infrastructure.models import OrderModel


class SqlAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: str) -> Order | None:
        model = await self._session.get(OrderModel, id)
        return self._to_domain(model) if model else None

    async def add(self, aggregate: Order) -> None:
        self._session.add(self._to_model(aggregate))

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Order]:
        result = await self._session.execute(select(OrderModel).limit(limit).offset(offset))
        return [self._to_domain(model) for model in result.scalars().all()]

    @staticmethod
    def _to_model(order: Order) -> OrderModel:
        return OrderModel(
            id=order.id,
            status=order.status.value,
            lines=[
                {"sku": l.sku, "quantity": l.quantity, "unit_price_cents": l.unit_price_cents}
                for l in order.lines
            ],
        )

    @staticmethod
    def _to_domain(model: OrderModel) -> Order:
        lines = [OrderLine(**line) for line in model.lines]
        return Order(id=model.id, lines=lines, status=OrderStatus(model.status))
