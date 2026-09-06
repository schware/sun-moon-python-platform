from __future__ import annotations

import json

import httpx

from batch_service.config import BatchServiceConfig
from batch_service.jobs.order_summary import (
    OrderServiceReader,
    OrderSummaryProcessor,
    run_order_summary_job,
)


def _all_orders_transport(all_orders: list[dict]) -> httpx.MockTransport:
    """A fake order-service: slices `all_orders` by the limit/offset query
    params the real GET /orders route accepts, with no real HTTP server or
    order-service process needed (per ADR-0008's fakes-over-real-infra
    testing philosophy)."""

    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(request.url.params.get("offset", "0"))
        limit = int(request.url.params.get("limit", "100"))
        page = all_orders[offset : offset + limit]
        return httpx.Response(200, json=page)

    return httpx.MockTransport(handler)


async def test_order_service_reader_paginates_until_exhausted():
    orders = [{"id": f"o{i}", "status": "created", "total_cents": 100} for i in range(5)]
    reader = OrderServiceReader("http://order-service.test", transport=_all_orders_transport(orders))

    page1 = await reader.read(2)
    page2 = await reader.read(2)
    page3 = await reader.read(2)

    assert [o["id"] for o in page1] == ["o0", "o1"]
    assert [o["id"] for o in page2] == ["o2", "o3"]
    assert [o["id"] for o in page3] == ["o4"]
    assert await reader.read(2) == []


async def test_order_summary_processor_skips_cancelled():
    processor = OrderSummaryProcessor()
    await processor.process(
        [
            {"id": "o1", "status": "created", "total_cents": 1000},
            {"id": "o2", "status": "cancelled", "total_cents": 500},
            {"id": "o3", "status": "created", "total_cents": 2000},
        ]
    )
    assert processor.running_count == 2
    assert processor.running_total_cents == 3000


async def test_run_order_summary_job_end_to_end(tmp_path):
    orders = [
        {"id": "o1", "status": "created", "total_cents": 1000},
        {"id": "o2", "status": "cancelled", "total_cents": 500},
        {"id": "o3", "status": "created", "total_cents": 2000},
    ]
    reader = OrderServiceReader("http://order-service.test", transport=_all_orders_transport(orders))

    config = BatchServiceConfig(
        chunk_size=2,
        records_file=str(tmp_path / "records.ndjson"),
        summary_file=str(tmp_path / "summary.json"),
        execution_report_file=str(tmp_path / "execution.json"),
    )

    status = await run_order_summary_job(config, reader=reader)

    assert status == 0

    records = (tmp_path / "records.ndjson").read_text().strip().splitlines()
    assert [json.loads(line)["id"] for line in records] == ["o1", "o2", "o3"]

    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["order_count"] == 2
    assert summary["total_revenue_cents"] == 3000

    execution = json.loads((tmp_path / "execution.json").read_text())
    assert execution["success"] is True
    assert execution["records_processed"] == 3
    assert execution["chunks_processed"] == 2  # chunk_size=2 over 3 orders -> 2 + 1


async def test_run_order_summary_job_reports_failure_when_reader_errors(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    reader = OrderServiceReader("http://order-service.test", transport=httpx.MockTransport(handler))
    config = BatchServiceConfig(
        records_file=str(tmp_path / "records.ndjson"),
        summary_file=str(tmp_path / "summary.json"),
        execution_report_file=str(tmp_path / "execution.json"),
    )

    status = await run_order_summary_job(config, reader=reader)

    assert status == 1
