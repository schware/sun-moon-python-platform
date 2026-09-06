"""Claude-backed provider. Imports `anthropic` lazily inside __init__ so a
service can depend on netframework-ai-agent without the `[anthropic]` extra
and simply not select this provider."""
from __future__ import annotations

from netframework_ai_agent.base import AgentResponse, Message, ToolSpec


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-sonnet-5") -> None:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "the 'anthropic' package is required for this provider — "
                "install with `uv pip install netframework-ai-agent[anthropic]`"
            ) from exc
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    @staticmethod
    def _to_anthropic_messages(messages: list[Message]) -> tuple[str | None, list[dict]]:
        system: str | None = None
        converted: list[dict] = []
        for m in messages:
            if m.role == "system":
                system = m.content
            elif m.role == "tool":
                converted.append(
                    {
                        "role": "user",
                        "content": [
                            {"type": "tool_result", "tool_use_id": m.tool_result_for or "", "content": m.content}
                        ],
                    }
                )
            elif m.role == "assistant" and m.tool_call:
                converted.append(
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": m.tool_call.get("id", m.tool_call["name"]),
                                "name": m.tool_call["name"],
                                "input": m.tool_call.get("arguments", {}),
                            }
                        ],
                    }
                )
            else:
                converted.append({"role": m.role, "content": m.content})
        return system, converted

    async def complete(self, messages: list[Message], tools: list[ToolSpec]) -> AgentResponse:
        system, converted = self._to_anthropic_messages(messages)
        tool_defs = [
            {"name": t.name, "description": t.description, "input_schema": t.parameters} for t in tools
        ]
        response = await self._client.messages.create(
            model=self._model, max_tokens=1024, system=system, messages=converted, tools=tool_defs or None
        )
        tool_use = next((b for b in response.content if b.type == "tool_use"), None)
        if tool_use is not None:
            return AgentResponse(
                message=Message(
                    role="assistant",
                    content="",
                    tool_call={"id": tool_use.id, "name": tool_use.name, "arguments": tool_use.input},
                ),
                is_final=False,
            )
        text = "".join(b.text for b in response.content if b.type == "text")
        return AgentResponse(message=Message(role="assistant", content=text), is_final=True)
