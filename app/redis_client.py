"""Redis 连接配置"""
import os
import redis.asyncio as redis
from typing import Optional

# Redis 连接 URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Redis 客户端实例
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """获取 Redis 客户端实例"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return _redis_client


async def close_redis():
    """关闭 Redis 连接"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
