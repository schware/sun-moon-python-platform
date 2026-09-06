*🇰🇷 한국어 버전: [0008-testing-with-fakes-instead-of-real-infra_kr.md](0008-testing-with-fakes-instead-of-real-infra_kr.md)*

# ADR-0008: Test with fakes/stubs instead of real infrastructure (Redis / other services)

- **Status**: Accepted
- **Date**: 2026-09-06
- **Deciders**: Claude (design proposal)

## Context

Once ADR-0005/0006 split services apart and moved communication to
HTTP/Redis, it had to be decided: "does running the tests require Redis and
every other service to be up?" This wasn't hypothetical — this dev
environment itself has no Docker/Redis installed, so the question was hit
directly during development.

## Decision

- **Unit/service tests inject fakes.** `order-service`'s tests inject
  `netframework_core.eventbus.local_bus.LocalEventBus` into the
  constructor instead of `RedisEventBus`, verifying in-memory what it
  actually tried to publish
  (`test_create_order_publishes_integration_event` in
  `services/order-service/tests/test_order_api.py`). `ai-agent-service`'s
  tests use `FakeOrderClient` instead of a real-HTTP `OrderServiceClient`,
  and `RecordingAssistant` instead of a real-agent `AssistantService`.
- **This is possible because both coupling points are
  constructor-injected interfaces** — the `EventBus` protocol, the
  `get_order` signature, the `.ask()` signature. That tests can be written
  this way is itself a side-effect check that the coupling points are
  properly abstracted.
- **Manual local verification (confirming real inter-process
  communication) is kept separate and heavier.** A `fakeredis.TcpFakeServer`
  (a pure-Python server implementing the actual Redis wire protocol) was
  used to run both service processes for real and confirm HTTP/Redis
  actually flow between them (`scripts/dev_redis.py`). This was not folded
  into the automated test suite — left as a manual/CI integration-test step.

## Alternatives considered

- **Spin up real Redis via testcontainers** — more realistic, but requires
  Docker, which isn't available in this environment directly. Recommended
  to add at the contract-test stage once CI has Docker (see README next steps).
- **Patch every call with a mocking library (unittest.mock)** — ties tests
  to internal implementation details, making them brittle under
  refactoring. A fake object (a real, minimal working implementation) was
  judged to verify the interface contract better.
- **Skip integration tests entirely** — rejected, since after splitting
  into services there would be zero way to verify "does this actually
  connect over the network." Instead, minimal evidence was captured outside
  the automated suite via a manual script (this conversation's execution logs).

## Consequences

- The pytest suites (9 tests, per service) **finish in a few seconds with
  no Redis and no Docker** — meaning a human coding directly can run
  `pytest` immediately without installing heavy infrastructure (see `CONTRIBUTING.md`).
- The tradeoff: someone has to keep verifying that the fakes accurately
  mimic real Redis/HTTP behavior. For example, `LocalEventBus` doesn't
  simulate ordering guarantees or network-failure scenarios — Redis-specific
  failure modes (dropped connections, reconnects) aren't caught by these tests.
- The automated suite has no test verifying "do the two services actually
  connect" — the only evidence for that right now is the one manual check
  done during this conversation. As the project grows, a
  `docker-compose`-based (or testcontainers-based) integration test job
  should be added to CI (README "Planned next steps").

## References

- Martin Fowler, *Mocks Aren't Stubs* (martinfowler.com) — the
  mock/stub/fake distinction and their respective tradeoffs.
- fakeredis project documentation — the scope/limits of what
  `TcpFakeServer` actually implements of the real Redis protocol.
