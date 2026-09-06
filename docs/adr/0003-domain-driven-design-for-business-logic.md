*🇰🇷 한국어 버전: [0003-domain-driven-design-for-business-logic_kr.md](0003-domain-driven-design-for-business-logic_kr.md)*

# ADR-0003: Structure business logic with DDD tactical patterns (Entity/Aggregate/Repository/UnitOfWork/Domain Event)

- **Status**: Accepted
- **Date**: 2026-09-06
- **Deciders**: Project owner (explicit request) + Claude (design proposal)

## Context

User request #2: "yesterday's focus was comms and DB — today, keep comms
and DB as the basics but integrate DDD concepts." "Use DDD" alone doesn't
produce code; which concrete patterns to adopt still had to be decided.

## Decision

Split each service (bounded context) into four layers:

- **domain/** — `Entity`, `AggregateRoot` (collects domain events, drained
  after commit), `ValueObject` (immutable, compared by value),
  `Repository` (abstract port) — base classes live in
  `libs/netframework-core/src/netframework_core/ddd/`. This layer imports
  no infrastructure at all (no SQLAlchemy, no FastAPI).
- **application/** — one method per use case. Opens a `UnitOfWork`, defines
  the transaction boundary. No business rules live here — those all live
  in the domain.
- **infrastructure/** — SQLAlchemy ORM models + Repository implementations.
  Implements domain's abstract interfaces.
- **interfaces/** — protocol-specific adapters: REST (FastAPI router), TCP, etc.

Dependency direction is always `interfaces → application → domain ←
infrastructure` (domain knows nothing about anything; infrastructure
conforms to domain — the same direction as Clean/Hexagonal Architecture).

The Order aggregate is the concrete example: `Order.create()` enforces an
invariant ("at least one line"), records an `OrderCreated` domain event, and
`SqlAlchemyUnitOfWork` drains and publishes that event only after the
commit succeeds.

## Alternatives considered

- **Transaction script (all logic in the service layer)** — yesterday's C
  service files were actually closer to this style. Faster to write, but
  conflicts with the explicit "integrate DDD" request.
  - **Note on rigor**: this codebase never independently validated this
    tradeoff — since the user explicitly asked for DDD, fulfilling the
    request took priority over a from-scratch alternatives comparison.
- **Active Record (use ORM models as domain objects directly, no
  aggregate)** — shorter to implement, but "where are invariants enforced"
  becomes fuzzy, and infrastructure (SQLAlchemy) leaks into the domain.
- **CQRS (separate command/query models, dedicated read model)** —
  overkill at the current scale (order CRUD). Revisit with a new ADR if
  reads grow and a read model becomes necessary.

## Consequences

- Even a small change (e.g. adding one field) touches four folders — an
  onboarding cost mitigated by CONTRIBUTING.md's "common tasks" section.
- Domain rules live in one place (the Aggregate), reducing the risk of the
  same rule being duplicated across a REST handler and a TCP handler.
- Only `Order` has been implemented in this pattern so far — whether the
  pattern actually holds up for a second domain is unproven. Adding
  `delivery-service` (README "Planned next steps") is meant to be the test of that.

## References

- Eric Evans, *Domain-Driven Design: Tackling Complexity in the Heart of
  Software* (2003) — the original source for Entity/Value
  Object/Aggregate/Repository.
- Vaughn Vernon, *Implementing Domain-Driven Design* (2013) — practical
  guidance on aggregate design rules (keep them small, one per
  transaction) and publishing domain events only after commit.
- Robert C. Martin, *Clean Architecture* (2017) / Alistair Cockburn,
  *Hexagonal Architecture* — the basis for the "domain doesn't know about
  infrastructure" dependency rule.
