from __future__ import annotations

from ai_agent_service.application.assistant_service import AssistantService


class FakeOrderClient:
    """Stands in for OrderServiceClient — no real HTTP call, no order-service
    process needed to test the agent loop's tool-calling mechanics."""

    async def get_order(self, order_id: str) -> str:
        return f'{{"id": "{order_id}", "status": "created", "total_cents": 1000}}'


def _make_service() -> AssistantService:
    return AssistantService(
        provider="echo", model="claude-sonnet-5", api_key=None, max_iterations=4, order_client=FakeOrderClient()
    )


async def test_ask_plain_question_uses_echo_provider():
    answer = await _make_service().ask("hello agent")
    assert answer == "[echo-agent] you said: hello agent"


async def test_ask_forces_get_order_tool_call():
    answer = await _make_service().ask('call:get_order {"order_id": "abc-123"}')
    assert "abc-123" in answer
    assert "created" in answer
