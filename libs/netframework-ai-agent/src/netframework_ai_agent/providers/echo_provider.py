"""Offline, deterministic provider — no API key needed. Convention for
exercising the tool-calling loop without a real LLM: send
"call:<tool_name> {json args}" as the question. Anything else is echoed
back as the final answer."""
from __future__ import annotations

import json

from netframework_ai_agent.base import AgentResponse, Message, ToolSpec


class EchoProvider:
    name = "echo"

    async def complete(self, messages: list[Message], tools: list[ToolSpec]) -> AgentResponse:
        last = messages[-1]

        if last.role == "tool":
            return AgentResponse(
                message=Message(role="assistant", content=f"[echo-agent] tool result: {last.content}"),
                is_final=True,
            )

        if last.role == "user" and last.content.startswith("call:"):
            _, _, rest = last.content.partition("call:")
            tool_name, _, args_json = rest.strip().partition(" ")
            arguments = json.loads(args_json) if args_json.strip() else {}
            return AgentResponse(
                message=Message(
                    role="assistant", content="", tool_call={"id": tool_name, "name": tool_name, "arguments": arguments}
                ),
                is_final=False,
            )

        return AgentResponse(
            message=Message(role="assistant", content=f"[echo-agent] you said: {last.content}"),
            is_final=True,
        )
