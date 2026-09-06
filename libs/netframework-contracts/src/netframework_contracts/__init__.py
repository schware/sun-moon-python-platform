"""Wire contracts shared across service boundaries.

This package must never depend on netframework-core, netframework-comms, or
any service — it holds only plain pydantic models (integration events,
cross-service request/response DTOs) plus the topic-name constants that go
with them. Every service that publishes or subscribes to a given topic
depends on this package instead of on each other, which is what lets
order-service and ai-agent-service be built, tested, and deployed by
different developers without either importing the other's code.

Treat a model here as a versioned public API: adding an optional field is
safe, renaming or removing one is a breaking change for every subscriber.
"""
