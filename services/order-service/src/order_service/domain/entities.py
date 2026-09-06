from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

from netframework_core.ddd.entity import AggregateRoot
from netframework_core.ddd.value_object import ValueObject
from netframework_core.exceptions import DomainError
from order_service.domain.events import OrderCreated


class OrderStatus(str, Enum):
    CREATED = "created"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class OrderLine(ValueObject):
    sku: str
    quantity: int
    unit_price_cents: int

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise DomainError("order line quantity must be positive")
        if self.unit_price_cents < 0:
            raise DomainError("order line unit price cannot be negative")

    @property
    def subtotal_cents(self) -> int:
        return self.quantity * self.unit_price_cents


class Order(AggregateRoot[str]):
    def __init__(self, id: str, lines: list[OrderLine], status: OrderStatus = OrderStatus.CREATED) -> None:
        super().__init__(id)
        if not lines:
            raise DomainError("an order must have at least one line")
        self.lines = lines
        self.status = status

    @classmethod
    def create(cls, lines: list[OrderLine]) -> "Order":
        order = cls(id=str(uuid4()), lines=lines)
        order.record_event(OrderCreated(order_id=order.id, total_cents=order.total_cents))
        return order

    def cancel(self) -> None:
        if self.status == OrderStatus.CANCELLED:
            raise DomainError("order is already cancelled")
        self.status = OrderStatus.CANCELLED

    @property
    def total_cents(self) -> int:
        return sum(line.subtotal_cents for line in self.lines)
