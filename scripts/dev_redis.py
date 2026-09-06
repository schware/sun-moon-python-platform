#!/usr/bin/env python3
"""Local-dev stand-in for Redis: an in-memory server that speaks the real
Redis wire protocol (via fakeredis), so both services can point REDIS_URL
at a real redis:// address without installing/running actual Redis or
Docker. Use `docker-compose.yml` (real Redis) for anything beyond a
laptop demo.

Usage:
    python scripts/dev_redis.py [port]   # default port 6379
"""
from __future__ import annotations

import sys

from fakeredis import TcpFakeServer


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 6379
    server_address = ("127.0.0.1", port)
    server = TcpFakeServer(server_address, server_type="redis")
    print(f"fake redis listening on redis://{server_address[0]}:{server_address[1]}")
    server.serve_forever()


if __name__ == "__main__":
    main()
