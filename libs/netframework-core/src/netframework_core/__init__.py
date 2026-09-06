"""netframework-core — the one shared kernel every service in this monorepo
depends on: config, logging, DDD base types (Entity/AggregateRoot/DomainEvent/
Repository/UnitOfWork), SQLAlchemy persistence helpers, and two distinct
event-bus concepts:

  ddd.event_bus     in-process only — drains an aggregate's domain events
                     after a successful commit, for same-service listeners.
  eventbus          cross-service — publishes/consumes *integration events*
                     (plain pydantic contracts from netframework-contracts)
                     over Redis pub/sub, so services never import each
                     other's domain code to react to what happened elsewhere.

Keeping these separate is deliberate: a domain event is an internal,
rich Python object that can change shape freely as one service evolves; an
integration event is a versioned wire contract other teams' services
depend on, and should change much more carefully.
"""
