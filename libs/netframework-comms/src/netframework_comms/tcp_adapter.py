"""Generic line-based TCP adapter (asyncio.start_server). Newline-delimited
text; the first whitespace-separated token is looked up in `handlers` and,
if found, that handler's return value is written back — otherwise the line
is echoed, so `nc <host> <port>` "just echoes" out of the box with no
handlers registered at all."""
from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

from netframework_core.logging import get_logger

logger = get_logger(__name__)

TcpHandler = Callable[[bytes], "bytes | Awaitable[bytes]"]


async def _handle_client(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, handlers: dict[str, TcpHandler]
) -> None:
    peer = writer.get_extra_info("peername")
    logger.debug("tcp_connected", peer=peer)
    try:
        while not reader.at_eof():
            line = await reader.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").rstrip("\r\n")
            if not text:
                continue
            command, _, rest = text.partition(" ")
            handler = handlers.get(command)
            if handler is not None:
                result = handler(rest.encode())
                if asyncio.iscoroutine(result):
                    result = await result
                reply = result if isinstance(result, (bytes, bytearray)) else str(result).encode()
            else:
                reply = line
            writer.write(reply if reply.endswith(b"\n") else reply + b"\n")
            await writer.drain()
    finally:
        writer.close()
        logger.debug("tcp_disconnected", peer=peer)


async def start_tcp_server(
    host: str, port: int, handlers: dict[str, TcpHandler] | None = None
) -> asyncio.base_events.Server:
    handlers = handlers or {}
    server = await asyncio.start_server(lambda r, w: _handle_client(r, w, handlers), host=host, port=port)
    logger.info("tcp_listening", host=host, port=port)
    return server
