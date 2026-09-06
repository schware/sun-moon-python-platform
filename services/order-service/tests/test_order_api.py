from __future__ import annotations

import httpx
from netframework_contracts.order_events import ORDER_CREATED_TOPIC, OrderCreatedEvent


async def test_create_and_get_order(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/orders", json={"lines": [{"sku": "WIDGET", "quantity": 2, "unit_price_cents": 500}]}
        )
        assert create_resp.status_code == 201
        order = create_resp.json()
        assert order["total_cents"] == 1000

        get_resp = await client.get(f"/orders/{order['id']}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == order["id"]

        assert (await client.get("/orders/does-not-exist")).status_code == 404
        assert len((await client.get("/orders")).json()) == 1


async def test_create_order_publishes_integration_event(app, integration_events):
    received: list[OrderCreatedEvent] = []

    async def on_order_created(event: OrderCreatedEvent) -> None:
        received.append(event)

    integration_events.subscribe(ORDER_CREATED_TOPIC, OrderCreatedEvent, on_order_created)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/orders", json={"lines": [{"sku": "GADGET", "quantity": 1, "unit_price_cents": 2500}]}
        )
    order_id = resp.json()["id"]

    assert len(received) == 1
    assert received[0].order_id == order_id
    assert received[0].total_cents == 2500
