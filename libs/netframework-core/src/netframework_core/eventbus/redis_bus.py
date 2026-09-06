"""Redis pub/sub backed EventBus — the real cross-service transport. One
Redis channel per topic; publish is fire-and-forget (no delivery guarantee,
no replay) which is the right tradeoff for a "notify other services /
AI agent about something that happened" use case. Swap for a durable queue
(e.g. RabbitMQ/Kafka) behind the same EventBus protocol if a future topic
needs at-least-once delivery or replay.
"""
from __future__ import annotations

import asyncio

from pydantic import BaseModel
from redis.asyncio import Redis

from netframework_core.eventbus.base import Handler
from netframework_core.logging import get_logger

logger = get_logger(__name__)


class RedisEventBus:
    def __init__(self, client: Redis) -> None:
        self._client = client
        self._subs: dict[str, tuple[type[BaseModel], list[Handler]]] = {}
        self._pubsub = None
        self._listen_task: asyncio.Task | None = None

    def subscribe(self, topic: str, model: type[BaseModel], handler: Handler) -> None:
        if topic not in self._subs:
            self._subs[topic] = (model, [])
        self._subs[topic][1].append(handler)

    async def publish(self, topic: str, message: BaseModel) -> None:
        await self._client.publish(topic, message.model_dump_json())

    async def start(self) -> None:
        if not self._subs:
            return
        self._pubsub = self._client.pubsub()
        await self._pubsub.subscribe(*self._subs.keys())
        self._listen_task = asyncio.create_task(self._listen())
        logger.info("redis_eventbus_started", topics=list(self._subs.keys()))

    async def _listen(self) -> None:
        assert self._pubsub is not None
        async for raw in self._pubsub.listen():
            if raw.get("type") != "message":
                continue
            topic = raw["channel"]
            entry = self._subs.get(topic)
            if entry is None:
                continue
            model, handlers = entry
            try:
                message = model.model_validate_json(raw["data"])
            except Exception as exc:  # noqa: BLE001
                logger.error("integration_event_decode_failed", topic=topic, error=str(exc))
                continue
            for handler in handlers:
                try:
                    await handler(message)
                except Exception as exc:  # noqa: BLE001
                    logger.error("integration_event_handler_failed", topic=topic, error=str(exc))

    async def stop(self) -> None:
        if self._listen_task:
            self._listen_task.cancel()
        if self._pubsub:
            await self._pubsub.aclose()
        await self._client.aclose()


def create_redis_bus(url: str) -> RedisEventBus:
    return RedisEventBus(Redis.from_url(url, decode_responses=True))
