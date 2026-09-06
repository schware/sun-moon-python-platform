*🇰🇷 Korean version: [0010-batch-service-design_kr.md](0010-batch-service-design_kr.md)*

# ADR-0010: `batch-service` design — a shared Job/Step/Chunk library, real HTTP pagination, config via env vars (not JSON)

- **Status**: Accepted
- **Date**: 2026-09-06
- **Deciders**: Project owner

## Context

The [`alignment`](https://github.com/schware/alignment) repo's ADR-0006
decided to build the same Batch design (Spring Batch's Job → Step → Chunk,
Reader/Processor/Writer) in both C (`sun-moon-c-server`, already done —
see that repo's ADR-0001) and Python, against the same `order-service`
REST contract. `order-service`'s `GET /orders` had no `limit`/`offset`
query params at the time the C side was built, so that implementation
fetches everything in one call and chunks client-side (an acknowledged,
temporary gap — see `sun-moon-c-server`'s ADR-0001, "Consequences").

## Decision

- **A new shared library, `libs/netframework-batch`** (not code embedded
  directly in `batch-service`): `Reader`/`Processor`/`Writer` `Protocol`s
  and `run_step()` — the Python counterpart to `sun-moon-c-server`'s
  `batch.h`/`batch.c`. Where C had to bundle function pointers into a
  struct (no interfaces in C), Python uses real `Protocol` generics; the
  chunk loop and fault-tolerant per-chunk failure handling
  (`JobResult.chunks_failed`/`records_failed`, a failed chunk logged and
  skipped rather than aborting the job) are otherwise the same design.
  Kept as its own `libs/` package rather than inlined in `batch-service`
  so a future second batch job doesn't have to duplicate the engine —
  matching this monorepo's existing libs/services split (ADR-0005).
- **`order-service`'s `GET /orders` gained `limit`/`offset` query
  params** (defaulting to the previous hardcoded values, so
  `ai-agent-service` and any other existing caller are unaffected). This
  makes `batch-service`'s reader genuinely chunk-bounded over HTTP — a
  real improvement over `sun-moon-c-server`'s interim fetch-everything
  approach, made possible because this work happens inside the same
  Python monorepo instead of needing a cross-repo API change first.
- **A new service, `services/batch-service`** (not a mode of
  `order-service`): `OrderServiceReader` (paginated HTTP reads),
  `OrderSummaryProcessor` (sums `total_cents`, skips cancelled orders —
  identical rule to the C job, for direct comparison), `NdjsonWriter`
  (streams one JSON line per order, chunk-bounded on the write side same
  as C). Output shape matches `sun-moon-c-server`'s exactly: one NDJSON
  records file, one JSON summary object, one JSON execution report.
- **Config via environment variables + `.env`** (`BatchServiceConfig`,
  extending `BaseServiceConfig` per ADR-0007) — **not** JSON, even though
  `sun-moon-c-server`'s `batch_runner` is JSON-configured. This is
  deliberate, not an inconsistency: the JSON-config instruction was scoped
  to "for C" specifically; within this repo, every service already
  configures itself the same way (ADR-0007), and `batch-service` follows
  suit rather than introducing a second config mechanism here.
- **A separate entrypoint** (`batch_service/main.py`, one `asyncio.run()`
  call, no FastAPI app) — mirrors `sun-moon-c-server`'s separate
  `batch_runner` binary and the reasoning in that repo's ADR-0001: a
  one-shot, sequential job has a different runtime shape than a
  long-running server, and shouldn't be squeezed into one.

## Alternatives considered

- **Put the Job/Step/Chunk engine directly in `batch-service` instead of a
  new `libs/` package** — less ceremony for a single job, but the whole
  point of this exercise (per `alignment`'s ADR-0004) is a *reusable*
  pattern; a second batch job later would either duplicate the engine or
  force an awkward refactor. Fixed cost now, avoids that later.
- **Leave `order-service`'s reader-side gap unfixed, matching C exactly
  for symmetry** — would make the two implementations more directly
  comparable line-for-line, but throws away a real, easy improvement
  available specifically because this side of the work happens inside the
  Python monorepo. The comparison note (see Consequences) covers the
  difference explicitly instead.
- **JSON config for `batch-service`, matching C** — rejected per the
  scoping note above; would also be the first JSON-configured service in
  a repo that otherwise standardized on ADR-0007's env-var approach.

## Consequences

- **Direct comparison with `sun-moon-c-server`'s order-summary job** (the
  concrete deliverable ADR-0006 asked for): same job semantics (sum
  non-cancelled `total_cents`), same output shape (NDJSON + JSON summary +
  JSON execution report), same fault-tolerance model (a failed chunk is
  logged and counted, not fatal) — but the Python reader is genuinely
  chunk-bounded over HTTP while the C reader still fetches everything in
  one call. That gap is now purely a `sun-moon-c-server`-side follow-up
  (its own README already tracks this), not blocked on anything here.
- `order-service`'s public REST contract now has three consumers
  (`ai-agent-service`, `batch-service`, and `sun-moon-c-server`'s
  `batch_runner`) instead of two — raises the bar on changing `GET
  /orders`'s response shape without checking all three, the same
  "contracts need versioning discipline" point already flagged in
  ADR-0006.
- `netframework-batch` currently has exactly one consumer
  (`batch-service`) — its Protocol-based design is unverified against a
  second, differently-shaped job; treat it as validated-by-one until that happens.
- No database dependency for `batch-service` at all — its state is the
  order data it reads over HTTP plus the files it writes; nothing to
  migrate, nothing to back up. A future job needing durable run history
  (a real Spring-Batch-style `JobRepository`) would be a deliberate
  addition, not a default.

## References

- `alignment/docs/adr/0006-dual-language-batch-via-shared-contract.md` —
  the cross-repo decision this implements.
- `sun-moon-c-server/docs/adr/0001-batch-job-design.md` — the C
  implementation this mirrors and compares against.
- `docs/adr/0006-inter-service-communication-http-and-redis.md` (this
  repo) — the REST-contract discipline this ADR's Consequences extend to
  a third/fourth consumer.
- `docs/adr/0007-config-via-environment-variables.md` (this repo) — why
  `batch-service` uses env vars, not JSON.
