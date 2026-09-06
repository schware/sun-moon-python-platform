*🇰🇷 한국어 버전: [README_kr.md](README_kr.md)*

# netframework monorepo — DDD services, comms, DB and an AI Agent

A **real monorepo of independently deployable services**, managed with
[uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/):
shared libraries under `libs/`, independently-deployable bounded-context
services under `services/`, one Redis for cross-service integration events,
one `pyproject.toml` at the root tying the whole workspace together for
local dev — but each service ships, versions, and scales on its own.

This replaces an earlier "modular monolith" draft of the same idea (one
process, in-memory event bus, plugin-loaded modules). That version is fine
for a single team in one codebase; this version is for the actual ask —
multiple developers, multiple teams, each owning a service end to end.

## Docs — rationale / coding this yourself / setting new rules

Most of this code was written by Claude. If you want to review or change
**why** it was decided this way, the following is faster than re-reading
this whole README:

- **[`docs/adr/`](docs/adr/)** — Architecture Decision Records, one per
  decision, each recording context/alternatives/sources. Language choice
  (ADR-0002), how DDD was applied (ADR-0003), the AI Agent design
  (ADR-0004), what triggered the monorepo pivot and the conversation
  context at that moment (ADR-0005), inter-service communication
  (ADR-0006), config approach (ADR-0007), testing strategy (ADR-0008) each
  get their own file. **If you disagree with a decision, start from that
  ADR's "Alternatives considered"** — it immediately shows whether it's an
  alternative that was already weighed, or one that got missed.
- **[`CONTRIBUTING.md`](CONTRIBUTING.md)** — a guide for coding this
  directly without Claude: how to decide where code goes, common-task
  recipes, coding conventions, and **who decides what as this scales from
  individual → team → project** (including the process for setting new rules).
- **[`CODEOWNERS`](CODEOWNERS)** — a per-path ownership template (currently
  placeholder `@team-*` entries — fill in once real owners are assigned).

**To set a new direction/rule**: copy `docs/adr/0000-template.md`, write a
new ADR, discuss it with the `CODEOWNERS` entries for the affected
service(s)/librar(y/ies), then flip its Status to `Accepted`. Reversing an
existing decision also means writing a new ADR with a "Supersedes" link
rather than editing the old file — keeping *what* changed and *why* on
record is what stops the next person (human or Claude) from repeating the
same trial and error.

## Layout

```
pyproject.toml                 # virtual workspace root — no code, just [tool.uv.workspace]
docker-compose.yml             # redis + both services, wired by env vars
scripts/dev_redis.py           # fakeredis-backed redis:// substitute for laptop dev (no Docker needed)

libs/                          # shared libraries — every service may depend on these
  netframework-core/           #   config, logging, exceptions, DDD base types, SQLAlchemy helpers,
                                #   two event buses (in-process DomainEventBus + cross-service EventBus)
  netframework-comms/          #   FastAPI app factory, asyncio TCP line-protocol, asyncio UDP echo
  netframework-ai-agent/       #   provider-agnostic tool-calling Agent loop + ToolRegistry
  netframework-contracts/      #   ONLY plain pydantic models for cross-service messages — no logic,
                                #   no dependency on anything else in this repo

services/                      # independently deployable — separate process, separate port, separate DB
  order-service/                #   domain/ application/ infrastructure/ interfaces/ + main.py
  ai-agent-service/              #   application/ interfaces/ events/ + main.py
```

## Why this is a monorepo, not a modular monolith

| | one process (previous draft) | this repo |
|---|---|---|
| Deploy unit | one process for everything | **one process per service** — `order-service` and `ai-agent-service` ship/scale/restart independently |
| Module → module call | Python function call, same memory | **HTTP** (sync read) or **Redis pub/sub** (async notification) |
| Shared code | one `netframework` package | `libs/*` — each an independently versioned package other services `uv add` |
| Cross-team coupling | shared `AppContext` object | `libs/netframework-contracts` — a models-only package; **no service ever imports another service's code** |
| Adding a service | add a module + one config line | add a `services/<name>/` package + one line in root `pyproject.toml`'s `[tool.uv.workspace] members` |

The rule that makes this work: **`order-service` and `ai-agent-service` never
import each other.** Every dependency between them is either (a) `libs/netframework-contracts`
(a shared *shape*, not shared *code*) or (b) a network call to the other
service's public REST API. That's what lets two different developers own
these two services without ever touching each other's pull requests.

## The two seams between services

1. **Synchronous read — HTTP.** `ai-agent-service`'s `get_order` tool
   (`services/ai-agent-service/src/ai_agent_service/application/order_client.py`)
   is a plain `httpx` call to `order-service`'s public `GET /orders/{id}`.
   If order-service is down, the tool call fails gracefully — the agent gets
   an error string back, not a crash.

2. **Asynchronous notification — Redis pub/sub.** After committing a new
   order, `order-service` publishes an `OrderCreatedEvent` (defined once in
   `netframework-contracts`) on the `order.created` topic
   (`services/order-service/src/order_service/application/services.py`).
   `ai-agent-service` subscribes to that same topic on startup
   (`services/ai-agent-service/src/ai_agent_service/events/order_events_handler.py`)
   and asks its agent to draft a one-line operational note. Neither service
   imports the other's domain model — only the shared `OrderCreatedEvent` shape.

Domain events vs. integration events, made concrete:
`order_service.domain.events.OrderCreated` (internal, drained by the
`UnitOfWork`, could grow any field order-service's own logic needs) is a
**different class** from `netframework_contracts.order_events.OrderCreatedEvent`
(external, the two fields ai-agent-service actually needs). The application
layer explicitly maps one to the other after commit — see
`OrderApplicationService.create_order`. This is deliberate: an internal
domain model should be free to change; a wire contract other teams depend
on should change much more carefully.

## Quick start (no Docker required)

Requires **Python 3.11+** and [uv](https://docs.astral.sh/uv/) (`pip install uv`).

```bash
uv sync --all-packages --extra dev      # resolves + installs the whole workspace once

# terminal 1 — a real-protocol, in-memory Redis stand-in (needs `pip install fakeredis`)
python scripts/dev_redis.py 6399

# terminal 2
REDIS_URL=redis://127.0.0.1:6399/0 \
  uv run --package order-service python -m order_service.main

# terminal 3
REDIS_URL=redis://127.0.0.1:6399/0 ORDER_SERVICE_BASE_URL=http://127.0.0.1:8081 \
  uv run --package ai-agent-service python -m ai_agent_service.main
```

Try it (verified end-to-end while building this — two real OS processes,
talking over real HTTP + a real Redis wire protocol):
```bash
curl -X POST http://localhost:8081/orders \
  -H 'Content-Type: application/json' \
  -d '{"lines":[{"sku":"WIDGET","quantity":2,"unit_price_cents":500}]}'

curl -X POST http://localhost:8082/assistant/ask \
  -H 'Content-Type: application/json' -d '{"question":"hello agent"}'

printf 'hello\nORDER_COUNT\n' | nc localhost 8090   # order-service's TCP adapter
```
Watch ai-agent-service's terminal after the `curl -X POST /orders` above —
an `ai_agent_order_note` log line appears, delivered purely through Redis.

## Quick start (Docker Compose — real Redis)

```bash
docker compose up --build
```
Same three services (`redis`, `order-service` on `:8081`/`:8090`,
`ai-agent-service` on `:8082`), wired by env vars instead of manual export.
*(Written to the standard uv-workspace-in-Docker pattern; not build-tested
in this environment since Docker isn't installed here — verify on first use.)*

## Tests

```bash
uv run --package order-service pytest services/order-service/tests
uv run --package ai-agent-service pytest services/ai-agent-service/tests
```
Both suites run with **no Redis and no cross-service network calls** —
`order-service`'s tests swap in `netframework_core.eventbus.local_bus.LocalEventBus`
and assert on what it *tried* to publish; `ai-agent-service`'s tests use a
`FakeOrderClient`/`RecordingAssistant` instead of real HTTP/agent calls.
This is only possible because both seams above are constructor-injected
interfaces, never hardcoded.

## Adding a new service

1. `services/<your-service>/` with the same shape as `order-service`
   (`domain/ application/ infrastructure/ interfaces/ + main.py + pyproject.toml`).
   `[tool.uv.workspace]` at the root already globs `services/*`, so it's
   picked up automatically — no root file to edit.
2. Depend on whichever `libs/*` you need via `[tool.uv.sources]` +
   `{ workspace = true }` (copy the pattern from an existing service's
   `pyproject.toml`).
3. Need to react to another service's event? Add the topic + pydantic model
   to `libs/netframework-contracts/` (or reuse an existing one) and
   `bus.subscribe(...)` in your own `events/` package — never import the
   other service's code.
4. Need to read another service's data synchronously? Write a small HTTP
   client against its public REST API (copy `order_client.py`'s shape).
5. `uv sync --all-packages` to pick it up locally; add it to
   `docker-compose.yml` for the containerized path.

## Open-source dependencies

uv (workspace/dependency management), FastAPI + Uvicorn (HTTP/WS), asyncio
(TCP/UDP), SQLAlchemy 2.0 async + aiosqlite (DB — swap the URL for
Postgres/MySQL per service), Redis (cross-service pub/sub) + fakeredis (local
dev without a real Redis), Pydantic v2 (DTOs/contracts/config), structlog,
httpx (inter-service HTTP), Anthropic SDK (optional, real agent reasoning).

## Planned next steps

- Alembic migrations per service (today: `create_all` on startup)
- A third service (e.g. `delivery-service`) to prove three services'
  events/contracts composing without any pairwise coupling
- An API gateway / BFF in front of both services' HTTP ports, mirroring
  yesterday's C "combined-server" convenience of one public port
- TLS for the TCP adapter and HTTPS for uvicorn per service
- CI: per-service test jobs that only run when that service (or a `libs/`
  dependency it uses) actually changed
- Transactional outbox for `order-service`'s integration-event publish —
  right now a commit can succeed while the follow-up Redis publish fails
  silently (see [ADR-0006](docs/adr/0006-inter-service-communication-http-and-redis.md)'s Consequences)
- Fill in real names/teams in [`CODEOWNERS`](CODEOWNERS) once ownership is decided
- A CI check that blocks merging a `libs/` or `netframework-contracts` change
  without a corresponding `docs/adr/` entry (today this is enforced by
  review discipline only, per [`CONTRIBUTING.md`](CONTRIBUTING.md))
