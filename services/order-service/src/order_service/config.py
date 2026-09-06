from __future__ import annotations

from netframework_core.config import BaseServiceConfig


class OrderServiceConfig(BaseServiceConfig):
    service_name: str = "order-service"
    http_port: int = 8081

    database_url: str = "sqlite+aiosqlite:///./data/order.db"
    database_echo: bool = False

    tcp_enabled: bool = True
    tcp_host: str = "0.0.0.0"
    tcp_port: int = 8090
