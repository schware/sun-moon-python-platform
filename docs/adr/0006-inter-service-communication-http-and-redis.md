*🇰🇷 한국어 버전: [0006-inter-service-communication-http-and-redis_kr.md](0006-inter-service-communication-http-and-redis_kr.md)*

# ADR-0006: Inter-service communication is sync HTTP (reads) + Redis pub/sub (async integration events); domain events and integration events are kept distinct

- **Status**: Accepted
- **Date**: 2026-09-06
- **Deciders**: Claude (design proposal, a follow-on to adopting ADR-0005)

## Context

ADR-0005 established that "services never import each other's code." That
meant deciding what actually replaces a direct call when two services need
to exchange information: `ai-agent-service` looking up a specific order
(request/response) and `order-service` announcing "an order was just
created" (event notification) are different in nature.

## Decision

**Split communication into two purpose-specific mechanisms:**

1. **Synchronous reads = HTTP.** `ai-agent-service`'s `get_order` tool
   calls order-service's public REST API (`GET /orders/{id}`) via `httpx`
   (`ai_agent_service/application/order_client.py`). On failure it returns
   an error string instead of raising, so the agent can degrade gracefully.

2. **Asynchronous notification = Redis pub/sub.** After committing a new
   order, `order-service` publishes an `OrderCreatedEvent` on the
   `order.created` topic; `ai-agent-service` subscribes to that topic at
   startup to receive it (`netframework_core.eventbus.redis_bus`).

3. **Domain event ≠ integration event, split explicitly.**
   `order_service.domain.events.OrderCreated` (internal, drained only
   within the same service by `UnitOfWork`) and
   `netframework_contracts.order_events.OrderCreatedEvent` (external, what
   another service actually receives) are deliberately different classes.
   The application layer (`OrderApplicationService.create_order`) maps the
   former to the latter explicitly after a successful commit — no
   automatic conversion or shared class.

4. **Contracts live only in `libs/netframework-contracts`** — plain
   pydantic models plus topic-name constants, importing no service code at all.

## Alternatives considered

- **Use HTTP for every inter-service interaction** — "an order was
  created" could instead be polled by ai-agent-service, or pushed via
  webhooks order-service sends to every known subscriber URL. Simpler to
  implement, but order-service would need to know who's subscribed,
  raising coupling and requiring order-service's code to change every time
  a subscriber is added. Pub/sub removes this coupling entirely —
  order-service never knows how many subscribers exist or who they are.
- **A proper message broker (Kafka/RabbitMQ)** — offers delivery
  guarantees (at-least-once) and replay, genuinely useful in production,
  but judged too much infrastructure cost for this stage. `RedisEventBus`
  sits behind the `EventBus` protocol specifically so the implementation
  can be swapped later without touching service code.
- **Publish the domain event as-is to other services (no translation)** —
  less code, but every change to order-service's internal domain model
  would break the contract with other services too. Keeping the two event
  types separate preserves "free to change internally, careful about
  changing externally."
- **Transactional Outbox pattern** — the textbook way to close the gap
  where a commit succeeds but the follow-up event publish fails, by
  bundling the DB write and the event write into one transaction. Not
  implemented this round — called out as a known risk below.

## Consequences

- **Known risk (no outbox)**: if `uow.commit()` succeeds in `create_order`
  but the immediately following `integration_events.publish(...)` fails
  (e.g. Redis is down), the order is saved but the notification is lost.
  This failure isn't currently handled — an outbox pattern or retry queue
  should be evaluated before taking real traffic (needs adding to README
  "Planned next steps").
- Redis pub/sub drops a published message if there's no subscriber at that
  moment (no replay) — it should only be used for notifications that are
  OK to miss. If a "must-be-processed" event shows up later, a new ADR
  superseding this one should change the broker.
- Made it possible to test without real Redis — verified by swapping the
  `EventBus` protocol for `LocalEventBus` (see ADR-0008).
- This communication layer has only been proven with exactly two services
  (order-service ↔ ai-agent-service). Whether the same pattern scales
  cleanly to a third service is unproven — adding `delivery-service`
  (README "Planned next steps") is meant to double as that test.

## References

- Chris Richardson, microservices.io — the *Database per Service*, *Domain
  Event*, and *Saga* patterns. The basis for "services never see each
  other's DB/code directly."
- Martin Fowler, *What do you mean by "Event-Driven"?* (martinfowler.com) —
  the distinction between event notification and event-carried state
  transfer. This project is closer to "event notification" (just an
  alert, not full state transfer).
- Chris Richardson, *Pattern: Transactional outbox* — the original source
  for the pattern explicitly noted above as "not applied." A candidate for the next step.
