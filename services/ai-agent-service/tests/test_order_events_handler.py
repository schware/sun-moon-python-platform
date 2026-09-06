from __future__ import annotations

from datetime import datetime, timezone

from netframework_contracts.order_events import ORDER_CREATED_TOPIC, OrderCreatedEvent
from netframework_core.eventbus.local_bus import LocalEventBus

from ai_agent_service.events.order_events_handler import register_order_event_handlers


class RecordingAssistant:
    """Duck-types AssistantService (only .ask is used) so this test exercises
    just the event-wiring, independent of the agent loop / provider."""

    def __init__(self) -> None:
        self.questions: list[str] = []

    async def ask(self, question: str) -> str:
        self.questions.append(question)
        return "noted"


async def test_order_created_triggers_assistant_note():
    bus = LocalEventBus()
    assistant = RecordingAssistant()
    register_order_event_handlers(bus, assistant)

    await bus.publish(
        ORDER_CREATED_TOPIC,
        OrderCreatedEvent(order_id="abc-123", total_cents=1000, occurred_at=datetime.now(timezone.utc)),
    )

    assert len(assistant.questions) == 1
    assert "abc-123" in assistant.questions[0]
    assert "1000" in assistant.questions[0]
