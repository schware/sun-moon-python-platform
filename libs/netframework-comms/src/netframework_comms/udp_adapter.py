"""UDP echo adapter (asyncio DatagramProtocol) — connectionless, single
socket. Not wired into either example service by default; available for a
future service that needs it (see README)."""
from __future__ import annotations

import asyncio

from netframework_core.logging import get_logger

logger = get_logger(__name__)


class _EchoProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport: asyncio.DatagramTransport) -> None:  # type: ignore[override]
        self.transport = transport

    def datagram_received(self, data: bytes, addr) -> None:  # type: ignore[override]
        self.transport.sendto(data, addr)


async def start_udp_server(host: str, port: int) -> asyncio.DatagramTransport:
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(_EchoProtocol, local_addr=(host, port))
    logger.info("udp_listening", host=host, port=port)
    return transport
