from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

_mongo_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    """Trả về MongoDB client singleton."""
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
    return _mongo_client


def get_db() -> AsyncIOMotorDatabase:
    """Trả về database instance."""
    return get_mongo_client()[settings.MONGODB_DB]


async def log_fraud_check(data: dict) -> None:
    """Ghi log kết quả fraud check vào collection `fraud_logs`."""
    db = get_db()
    await db["fraud_logs"].insert_one(data)


async def log_delivery(data: dict) -> None:
    """Ghi log delivery estimate vào collection `delivery_logs`."""
    db = get_db()
    await db["delivery_logs"].insert_one(data)
