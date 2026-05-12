import json
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)
redis_client = None


async def get_redis():
    global redis_client
    if not settings.REDIS_URL:
        return None
    if redis_client is None:
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


async def get_cache(key: str) -> Any | None:
    if not settings.REDIS_URL:
        return None
    client = await get_redis()
    if client is None:
        return None
    value = await client.get(key)
    if value:
        return json.loads(value)
    return None


async def set_cache(key: str, value: Any, ttl: int = 3600) -> None:
    if not settings.REDIS_URL:
        return
    client = await get_redis()
    if client is not None:
        await client.set(key, json.dumps(value), ex=ttl)