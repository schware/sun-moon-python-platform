from __future__ import annotations

from netframework_ai_agent.base import Agent, ToolSpec
from netframework_ai_agent.factory import build_provider
from netframework_ai_agent.tool_registry import ToolRegistry

from ai_agent_service.application.order_client import OrderServiceClient

SYSTEM_PROMPT = (
    "You are an internal operations assistant. Use the get_order tool whenever "
    "a question references a specific order id. Keep answers to one or two sentences."
)


class AssistantService:
    def __init__(
        self,
        *,
        provider: str,
        model: str,
        api_key: str | None,
        max_iterations: int,
        order_client: OrderServiceClient,
    ) -> None:
        tools = ToolRegistry()
        tools.register(
            ToolSpec(
                name="get_order",
                description="Look up one order by id; returns its status, total (cents) and line items.",
                parameters={
                    "type": "object",
                    "properties": {"order_id": {"type": "string"}},
                    "required": ["order_id"],
                },
                handler=order_client.get_order,
            )
        )
        self._agent = Agent(
            build_provider(provider, model=model, api_key=api_key), tools, max_iterations=max_iterations
        )

    async def ask(self, question: str) -> str:
        return await self._agent.run(question, system=SYSTEM_PROMPT)
