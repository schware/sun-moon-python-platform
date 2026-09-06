from __future__ import annotations

import json
from datetime import datetime

from netframework_batch.engine import JobResult


def write_execution_report(
    path: str,
    *,
    job_name: str,
    chunk_size: int,
    result: JobResult,
    started_at: datetime,
    finished_at: datetime,
) -> None:
    """Writes a JSON execution report — the Python counterpart to
    sun-moon-c-server's batch_write_execution_report(). Same fields, same
    shape, so the two implementations' output is directly comparable."""
    report = {
        "job_name": job_name,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "chunk_size": chunk_size,
        "chunks_processed": result.chunks_processed,
        "chunks_failed": result.chunks_failed,
        "records_processed": result.records_processed,
        "records_failed": result.records_failed,
        "success": result.success,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
