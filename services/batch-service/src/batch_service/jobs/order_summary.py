"""The order-summary batch job: reads orders from order-service over HTTP,
then reads/processes/writes them through the generic Job/Step/Chunk engine
(netframework_batch.engine) -- see this service's ADR-0010, and
sun-moon-c-server's ADR-0001 for the C implementation this mirrors."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Sequence

import httpx
from netframework_batch.engine import run_step
from netframework_batch.report import write_execution_report
from netframework_core.logging import get_logger

from batch_service.config import BatchServiceConfig

logger = get_logger(__name__)

OrderRecord = dict[str, Any]


class OrderServiceReader:
    """Reads order-service's GET /orders one page at a time via limit/offset
    query params -- genuinely chunk-bounded over HTTP, unlike
    sun-moon-c-server's reader (which fetches everything in one call; see
    that repo's ADR-0001 "Consequences") now that order-service supports
    pagination (added alongside this job specifically for that reason)."""

    def __init__(self, base_url: str, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._transport = transport
        self._offset = 0
        self._exhausted = False

    async def read(self, max_count: int) -> Sequence[OrderRecord]:
        if self._exhausted:
            return []

        async with httpx.AsyncClient(
            base_url=self._base_url, transport=self._transport, timeout=10.0
        ) as client:
            response = await client.get("/orders", params={"limit": max_count, "offset": self._offset})
            response.raise_for_status()
            page: list[OrderRecord] = response.json()

        if len(page) < max_count:
            self._exhausted = True
        self._offset += len(page)
        return page


class OrderSummaryProcessor:
    """Sums revenue (total_cents), skipping cancelled orders — the same
    rule as sun-moon-c-server's order_summary_batch_job.c, so the two
    implementations' output is directly comparable."""

    def __init__(self) -> None:
        self.running_total_cents = 0
        self.running_count = 0

    async def process(self, chunk: Sequence[OrderRecord]) -> Sequence[OrderRecord]:
        for order in chunk:
            if order["status"] == "cancelled":
                continue
            self.running_total_cents += order["total_cents"]
            self.running_count += 1
        return chunk


class NdjsonWriter:
    """Streams each order as one line of NDJSON — genuinely chunk-bounded
    on the write side (nothing held in memory across chunks), matching
    sun-moon-c-server's writer."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._file = None

    def open(self) -> None:
        self._file = open(self._path, "w", encoding="utf-8")

    async def write(self, chunk: Sequence[OrderRecord]) -> None:
        assert self._file is not None, "NdjsonWriter.open() must be called first"
        for order in chunk:
            line = {"id": order["id"], "status": order["status"], "total_cents": order["total_cents"]}
            self._file.write(json.dumps(line) + "\n")
        self._file.flush()

    def close(self) -> None:
        if self._file:
            self._file.close()
            self._file = None


async def run_order_summary_job(
    config: BatchServiceConfig,
    *,
    reader: OrderServiceReader | None = None,
) -> int:
    """Runs the order-summary job end to end. Returns 0 on success, 1 if
    any chunk failed *or* the reader itself failed (e.g. order-service
    unreachable) — the reader is not wrapped in the engine's per-chunk
    fault tolerance, matching sun-moon-c-server's batch_step_run(), where a
    reader failure aborts the job rather than being logged and skipped.

    `reader` is injectable for tests (see tests/test_order_summary_job.py)
    — production code (main.py) always calls this with the default, which
    builds a real OrderServiceReader against config.order_service_base_url.
    """
    started_at = datetime.now(timezone.utc)
    reader = reader or OrderServiceReader(config.order_service_base_url)
    processor = OrderSummaryProcessor()
    writer = NdjsonWriter(config.records_file)
    writer.open()

    try:
        result = await run_step(
            config.job_name, reader, writer, chunk_size=config.chunk_size, processor=processor
        )
    except Exception as exc:  # noqa: BLE001 - job-level fatal error, mirrors the C reader-failure path
        logger.error("order_summary_job_reader_failed", error=str(exc))
        writer.close()
        return 1
    writer.close()

    finished_at = datetime.now(timezone.utc)

    summary = {
        "job_name": config.job_name,
        "generated_at": finished_at.isoformat(),
        "order_count": processor.running_count,
        "total_revenue_cents": processor.running_total_cents,
    }
    with open(config.summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    write_execution_report(
        config.execution_report_file,
        job_name=config.job_name,
        chunk_size=config.chunk_size,
        result=result,
        started_at=started_at,
        finished_at=finished_at,
    )

    logger.info(
        "order_summary_job_done",
        chunks_processed=result.chunks_processed,
        chunks_failed=result.chunks_failed,
        records_processed=result.records_processed,
        records_failed=result.records_failed,
        total_revenue_cents=processor.running_total_cents,
        order_count=processor.running_count,
    )

    return 0 if result.success else 1
