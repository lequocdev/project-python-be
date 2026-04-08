import redis.asyncio as aioredis
from app.config import settings

_redis_client: aioredis.Redis | None = None


async def get_redis_client() -> aioredis.Redis:
    """Trả về Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def get_key(key: str) -> str | None:
    """Lấy giá trị theo key."""
    client = await get_redis_client()
    return await client.get(key)


async def set_key(key: str, value: str, ttl: int = 300) -> None:
    """Lưu giá trị với TTL (giây)."""
    client = await get_redis_client()
    await client.set(key, value, ex=ttl)


async def increment_counter(key: str, ttl: int = 3600) -> int:
    """
    Tăng counter và đặt TTL nếu key chưa tồn tại.
    Dùng cho velocity check (ví dụ: đếm đơn của user trong 1 giờ).
    """
    client = await get_redis_client()
    count = await client.incr(key)
    if count == 1:
        # Chỉ set TTL lần đầu tạo key
        await client.expire(key, ttl)
    return count
