"""Provider-agnostic agent loop. `Agent.run()` is the same tool-calling loop
regardless of which LLM answers it — swap EchoProvider (offline,
deterministic, for tests/dev) for AnthropicProvider without changing a
service's code, since services only ever depend on the LLMProvider Protocol.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Protocol

if TYPE_CHECKING:
    from netframework_ai_agent.tool_registry import ToolRegistry


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tool_call: dict[str, Any] | None = None  # {"id":, "name":, "arguments":}
    tool_result_for: str | None = None  # id of the tool_call this result answers


@dataclass
class AgentResponse:
    message: Message
    is_final: bool


class LLMProvider(Protocol):
    name: str

    async def complete(self, messages: list[Message], tools: list["ToolSpec"]) -> AgentResponse: ...


ToolHandler = Callable[..., Awaitable[str]]


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema for the tool's arguments
    handler: ToolHandler = field(repr=False)


class Agent:
    """Runs the classic think -> (optionally call a tool) -> think loop."""

    def __init__(self, provider: LLMProvider, tools: "ToolRegistry", max_iterations: int = 4) -> None:
        self.provider = provider
        self.tools = tools
        self.max_iterations = max_iterations

    async def run(self, user_input: str, *, system: str | None = None) -> str:
        messages: list[Message] = []
        if system:
            messages.append(Message(role="system", content=system))
        messages.append(Message(role="user", content=user_input))

        for _ in range(self.max_iterations):
            response = await self.provider.complete(messages, self.tools.specs())
            messages.append(response.message)
            if response.is_final:
                return response.message.content
            call = response.message.tool_call or {}
            result = await self.tools.invoke(call.get("name", ""), call.get("arguments", {}))
            messages.append(
                Message(role="tool", content=result, tool_result_for=call.get("id", call.get("name")))
            )
        return "agent stopped: max tool-call iterations reached"
