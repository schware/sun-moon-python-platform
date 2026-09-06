from __future__ import annotations

from netframework_comms.tcp_adapter import TcpHandler
from order_service.application.services import OrderApplicationService


def create_tcp_handlers(service: OrderApplicationService) -> dict[str, TcpHandler]:
    async def order_count(_: bytes) -> bytes:
        orders = await service.list_orders()
        return f"ORDER_COUNT {len(orders)}".encode()

    return {"ORDER_COUNT": order_count}
