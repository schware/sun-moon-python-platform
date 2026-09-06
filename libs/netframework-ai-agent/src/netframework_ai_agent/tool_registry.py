from __future__ import annotations

from netframework_ai_agent.base import ToolSpec


class ToolRegistry:
    """Tools a service exposes to its agent loop. In this monorepo,
    ai-agent-service registers a `get_order` tool whose handler is an HTTP
    call to order-service (see application/order_client.py) — the registry
    itself has no idea whether a tool is local or a network call."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def specs(self) -> list[ToolSpec]:
        return list(self._tools.values())

    async def invoke(self, name: str, arguments: dict) -> str:
        spec = self._tools.get(name)
        if spec is None:
            return f"error: unknown tool '{name}'"
        return await spec.handler(**arguments)
