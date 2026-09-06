from __future__ import annotations

import pytest
from netframework_core.exceptions import DomainError

from order_service.domain.entities import Order, OrderLine
from order_service.domain.events import OrderCreated


def test_order_create_records_event_and_computes_total():
    order = Order.create([OrderLine(sku="WIDGET", quantity=2, unit_price_cents=500)])

    events = order.pull_events()

    assert len(events) == 1
    assert isinstance(events[0], OrderCreated)
    assert events[0].order_id == order.id
    assert order.total_cents == 1000
    assert order.pull_events() == []


def test_order_requires_at_least_one_line():
    with pytest.raises(DomainError):
        Order.create([])


def test_order_line_rejects_non_positive_quantity():
    with pytest.raises(DomainError):
        OrderLine(sku="WIDGET", quantity=0, unit_price_cents=500)


def test_cancel_twice_raises():
    order = Order.create([OrderLine(sku="WIDGET", quantity=1, unit_price_cents=100)])
    order.cancel()
    with pytest.raises(DomainError):
        order.cancel()
