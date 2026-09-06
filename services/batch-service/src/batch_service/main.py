#!/usr/bin/env python3
"""batch-service entrypoint. Run with:

    uv run --package batch-service python -m batch_service.main

A plain one-shot script — one asyncio.run() call, no FastAPI app, no
long-running event loop. Mirrors sun-moon-c-server's batch_runner: a
separate, synchronous-in-spirit CLI, not a server, and not a mode of
order-service. See this service's ADR-0010 and sun-moon-c-server's
ADR-0001 for why batch work gets its own entrypoint.
"""
from __future__ import annotations

import asyncio
import sys

from dotenv import load_dotenv
from netframework_core.logging import configure_logging, get_logger

from batch_service.config import BatchServiceConfig
from batch_service.jobs.order_summary import run_order_summary_job

logger = get_logger(__name__)


async def main() -> int:
    load_dotenv()
    config = BatchServiceConfig()
    configure_logging(config.log_level, service_name=config.service_name)

    logger.info(
        "batch_service_starting",
        job_name=config.job_name,
        order_service_base_url=config.order_service_base_url,
        chunk_size=config.chunk_size,
    )
    return await run_order_summary_job(config)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
