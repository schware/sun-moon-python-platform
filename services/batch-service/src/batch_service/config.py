from __future__ import annotations

from netframework_core.config import BaseServiceConfig


class BatchServiceConfig(BaseServiceConfig):
    """Config via env vars + .env, per ADR-0007 — deliberately *not* JSON,
    even though sun-moon-c-server's batch_runner is JSON-configured. Each
    repo keeps its own already-established convention (see this service's
    own ADR-0010) rather than forcing one config mechanism across two
    otherwise-independent codebases."""

    service_name: str = "batch-service"

    order_service_base_url: str = "http://localhost:8081"
    chunk_size: int = 5

    job_name: str = "order_daily_summary"
    records_file: str = "reports/order_daily_summary.ndjson"
    summary_file: str = "reports/order_daily_summary_summary.json"
    execution_report_file: str = "reports/order_daily_summary_execution.json"
