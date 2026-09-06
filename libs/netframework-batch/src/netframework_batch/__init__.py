"""Generic Job/Step/Chunk batch engine — the Python counterpart to
sun-moon-c-server's batch.h/batch.c (see that repo's ADR-0001 and this
project's own ADR-0010). Reader/Processor/Writer are Protocols instead of
C's struct-of-function-pointers, since Python has real interfaces; the
chunk loop, fault-tolerant per-chunk failure handling, and JobResult
counters are otherwise the same design in both languages."""
