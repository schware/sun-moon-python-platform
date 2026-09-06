*🇰🇷 한국어 버전: [CONTRIBUTING_kr.md](CONTRIBUTING_kr.md)*

# Contributing Guide — for when a human codes this directly

This document exists for "I need to code this myself, without Claude." The
reasoning behind *why* it's structured this way lives in
[`docs/adr/`](docs/adr/); this file focuses on "what actually goes where, and how."

## 0. Before you start

- **Python 3.11 or newer.** Check with `python3 --version`. The machine
  this project was built on defaults `python` to Anaconda 3.8, which does
  not run this code as-is (fails immediately at pydantic model definition)
  — something like WSL's `python3.12` was used instead (basis:
  [ADR-0002](docs/adr/0002-python-as-implementation-language.md)).
- **[uv](https://docs.astral.sh/uv/)** installed: `uv --version`. If not,
  `pip install uv`.
- First time: run `uv sync --all-packages --extra dev` once from the root —
  re-run it only when a `services/*/pyproject.toml` changes.

If stuck: README.md's "Quick start" contains a command sequence that was
actually run and verified while building this repo.

## 1. Deciding where code goes

```
Is this change...
├─ Contained inside one service?
│   ├─ Business rule (invariant, state transition) → services/<x>/domain/
│   ├─ Use-case flow (transaction boundary, DTO mapping) → services/<x>/application/
│   ├─ DB / external API access → services/<x>/infrastructure/
│   └─ Protocol handler (REST/TCP/...) → services/<x>/interfaces/
├─ Reusable code multiple services need identically?
│   → libs/netframework-core (config/logging/DDD base types/DB/event bus),
│      libs/netframework-comms (protocol adapters),
│      libs/netframework-ai-agent (agent loop)
│   ⚠️  Changing libs/ affects every consuming service → ADR required (see CODEOWNERS)
├─ A new event/DTO exchanged between services?
│   → add a pydantic model to libs/netframework-contracts
│   ⚠️  Also requires an ADR — breaking a contract silently breaks another service
└─ An entirely new bounded context (domain)?
    → create services/<new-service>/. See README.md "Adding a new service"
```

Dependency-direction rule (do not violate — see
[ADR-0003](docs/adr/0003-domain-driven-design-for-business-logic.md)):
`interfaces → application → domain ← infrastructure`.
**Code inside `domain/` must not know SQLAlchemy or FastAPI exist.** If an
import statement there mentions `sqlalchemy` or `fastapi`, the layering is wrong.

## 2. Common tasks

**Add a new REST endpoint** (e.g. `PATCH /orders/{id}/cancel` on order-service)
1. Add a use-case method in `application/services.py`
   (`OrderApplicationService.cancel_order`) — open a UnitOfWork, call the
   domain method (`order.cancel()`), commit.
2. Add the route in `interfaces/rest.py`, calling that method.
3. Add success/failure cases to `tests/test_order_api.py`.

**Add a new domain invariant** (e.g. "orders over $10,000 need approval")
1. Check it inside an aggregate method in `domain/entities.py`, raising
   `netframework_core.exceptions.DomainError` on violation.
2. Add a `pytest.raises(DomainError)` case to `tests/test_order_domain.py`
   — application/infrastructure should need no changes at all; that's the
   point of keeping invariants in the domain.

**Add a new AI agent tool**
1. In the owning service's `module.py`/composition code:
   `ToolRegistry.register(ToolSpec(name=..., description=..., parameters=<JSON
   schema>, handler=<async fn>))`.
2. To let another service use that tool, build an HTTP client against the
   owning service's public API — the same shape as order-service's
   `get_order` pattern (`ai_agent_service/application/order_client.py`).
   **Never import the other service's code.**

**Add a new cross-service event** (e.g. `OrderCancelled`)
1. First, write an ADR at `docs/adr/000N-...md` (Status: Proposed) — which
   service needs it and why.
2. Add a pydantic model + topic constant to `libs/netframework-contracts/`.
3. Publishing service: after commit, translate the domain event into this
   contract model and call
   `integration_events.publish(TOPIC, ContractModel(...))`.
4. Subscribing service: add a handler in its `events/` package,
   `bus.subscribe(TOPIC, ContractModel, handler)`.
5. Flip the ADR's Status to `Accepted` and merge.

**Add a new service**: follow README.md's "Adding a new service" section as-is.

## 3. Coding conventions

- `from __future__ import annotations` at the top of every new file.
- Type hints always — a PR with a function signature missing arg/return
  types is grounds for rejection.
- Comments explain **why** only. Don't restate **what** the code already
  says (name things well instead).
- Tests must run without real Redis or other services — inject a
  Fake/Stub through the constructor (basis:
  [ADR-0008](docs/adr/0008-testing-with-fakes-instead-of-real-infra.md)).
  See the `LocalEventBus` pattern in
  `services/order-service/tests/conftest.py`.
- At minimum before committing/opening a PR:
  `uv run --package <service> pytest <service>/tests`.

## 4. Scaling from individual → team → project

This repo was designed with all three stages in mind
([ADR-0005](docs/adr/0005-monorepo-of-independent-services-via-uv-workspace.md)):

**Working solo**: run just one service locally. `AI_PROVIDER=echo` (no API
key needed), sqlite, and `scripts/dev_redis.py` (no Docker needed) let the
whole stack run on one laptop. That service's pytest suite is
self-contained and passes even with no other services present.

**Scaling to a team**: one team owns one (or several) services outright.
**Inside that service's domain/application/infrastructure/interfaces is the
team's own call** — free to refactor without another team's approval. What
it *can't* freely change is that service's **public contract** (its REST
response shapes, the event shapes it publishes in
`netframework-contracts`) — other services depend on that shape. The
`CODEOWNERS` file nails down "who has to approve changes to this path" as
code (currently placeholder team names — once real owners are assigned,
replace the `@team-*` entries with real GitHub usernames/teams).

**Scaling to a project (multiple teams)**: a decision to change something
shared across teams — `libs/` or `netframework-contracts` — can't be made
unilaterally by one team. **Write an ADR, get sign-off from every affected
service's owner** (exactly the process in
[ADR-0001](docs/adr/0001-use-adrs-for-decisions.md)). This is the concrete
answer to "how do we set basic ground rules for direction": not a single
line decided once, but a repeatable cycle — **propose (ADR draft) →
stakeholder review → agreement → flip Status to Accepted**. Need a new rule
later? Run the cycle again.

## 5. Handing this back to Claude

If a future conversation hands this project back to Claude, have it read
this file and everything in `docs/adr/` first — that stops Claude from
re-proposing an alternative that was already considered and rejected. A
one-liner like "read ADR-0005/0006 first, then start" is enough.
