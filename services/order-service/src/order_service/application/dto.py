from __future__ import annotations

from pydantic import BaseModel


class OrderLineDTO(BaseModel):
    sku: str
    quantity: int
    unit_price_cents: int


class CreateOrderRequest(BaseModel):
    lines: list[OrderLineDTO]


class OrderResponse(BaseModel):
    id: str
    status: str
    total_cents: int
    lines: list[OrderLineDTO]
