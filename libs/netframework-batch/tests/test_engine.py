from __future__ import annotations

from netframework_batch.engine import run_step


class FakeReader:
    """Hands out fixed-size pages from a list, then signals exhaustion."""

    def __init__(self, items: list[int]) -> None:
        self._items = items
        self._cursor = 0

    async def read(self, max_count: int) -> list[int]:
        if self._cursor >= len(self._items):
            return []
        chunk = self._items[self._cursor : self._cursor + max_count]
        self._cursor += len(chunk)
        return chunk


class RecordingWriter:
    def __init__(self) -> None:
        self.written: list[list[int]] = []

    async def write(self, chunk: list[int]) -> None:
        self.written.append(list(chunk))


class FailOnValueProcessor:
    """Raises when a chunk contains `bad_value` — used to test that one
    failed chunk doesn't abort the whole job."""

    def __init__(self, bad_value: int) -> None:
        self._bad_value = bad_value

    async def process(self, chunk: list[int]) -> list[int]:
        if self._bad_value in chunk:
            raise ValueError("poisoned chunk")
        return chunk


async def test_run_step_chunks_correctly():
    reader = FakeReader([1, 2, 3, 4, 5])
    writer = RecordingWriter()

    result = await run_step("test", reader, writer, chunk_size=2)

    assert writer.written == [[1, 2], [3, 4], [5]]
    assert result.chunks_processed == 3
    assert result.records_processed == 5
    assert result.chunks_failed == 0
    assert result.success is True


async def test_run_step_continues_after_a_failed_chunk():
    reader = FakeReader([1, 2, 3, 4, 5, 6])
    writer = RecordingWriter()
    processor = FailOnValueProcessor(bad_value=3)

    result = await run_step("test", reader, writer, chunk_size=2, processor=processor)

    # [1,2] ok, [3,4] fails (poisoned), [5,6] ok -- the failure doesn't stop the loop
    assert writer.written == [[1, 2], [5, 6]]
    assert result.chunks_processed == 2
    assert result.chunks_failed == 1
    assert result.records_processed == 4
    assert result.records_failed == 2
    assert result.success is False


async def test_run_step_on_empty_source():
    reader = FakeReader([])
    writer = RecordingWriter()

    result = await run_step("test", reader, writer, chunk_size=10)

    assert writer.written == []
    assert result.chunks_processed == 0
    assert result.success is True
