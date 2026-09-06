"""HTTP client for order-service's public REST API — this is the *entire*
coupling between the two services on the synchronous-read path. No shared
code, no shared database; if this call fails, ai-agent-service degrades
(the tool returns an error string to the agent) instead of crashing.
"""
from __future__ import annotations

import httpx


class OrderServiceClient:
    def __init__(self, base_url: str, *, timeout: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def get_order(self, order_id: str) -> str:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
            try:
                response = await client.get(f"/orders/{order_id}")
            except httpx.HTTPError as exc:
                return f"error: could not reach order-service ({exc})"
        if response.status_code == 404:
            return f"error: order {order_id} not found"
        response.raise_for_status()
        return response.text  # already JSON — passed straight through to the agent
