from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, TypeVar

from netframework_core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class Reader(Protocol[T]):
    async def read(self, max_count: int) -> Sequence[T]:
        """Returns up to max_count items; an empty sequence means exhausted."""
        ...


class Processor(Protocol[T]):
    async def process(self, chunk: Sequence[T]) -> Sequence[T]:
        """Transforms/validates a chunk. Raising fails the whole chunk —
        it's logged and counted, the job continues to the next chunk."""
        ...


class Writer(Protocol[T]):
    async def write(self, chunk: Sequence[T]) -> None:
        """Persists/emits a chunk. Raising fails the whole chunk."""
        ...


@dataclass
class JobResult:
    chunks_processed: int = 0
    chunks_failed: int = 0
    records_processed: int = 0
    records_failed: int = 0

    @property
    def success(self) -> bool:
        return self.chunks_failed == 0


async def run_step(
    name: str,
    reader: Reader[T],
    writer: Writer[T],
    *,
    chunk_size: int,
    processor: Processor[T] | None = None,
) -> JobResult:
    """Runs one Job/Step/Chunk step to completion: read() repeatedly (up to
    chunk_size items per call) -> process() -> write(), accumulating a
    JobResult. A chunk that raises during processing/writing is logged and
    counted as failed rather than aborting the whole job — the same
    fault-tolerant, chunk-oriented behavior as Spring Batch (and as
    sun-moon-c-server's batch_step_run(), see that repo's ADR-0001).
    """
    result = JobResult()

    while True:
        chunk = await reader.read(chunk_size)
        if not chunk:
            break

        try:
            if processor is not None:
                chunk = await processor.process(chunk)
            await writer.write(chunk)
        except Exception as exc:  # noqa: BLE001 - a failed chunk must not abort the job
            logger.error("batch_chunk_failed", step=name, error=str(exc))
            result.chunks_failed += 1
            result.records_failed += len(chunk)
            continue

        result.chunks_processed += 1
        result.records_processed += len(chunk)

    logger.info(
        "batch_step_done",
        step=name,
        chunks_processed=result.chunks_processed,
        chunks_failed=result.chunks_failed,
        records_processed=result.records_processed,
        records_failed=result.records_failed,
    )
    return result
