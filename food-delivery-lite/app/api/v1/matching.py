from fastapi import APIRouter
from app.schemas.matching import MatchingRequest, MatchingResponse
from app.services import matching_service
from app.database import redis as redis_db
from app.utils.logger import get_logger
import json

router = APIRouter()
logger = get_logger(__name__)

CACHE_TTL = 120  # 2 phút


@router.post("/score", response_model=MatchingResponse)
async def score_matching(req: MatchingRequest):
    """POST /api/v1/matching/score – Xếp hạng shipper cho đơn hàng."""
    logger.info(f"Matching score: order_id={req.order_id}, shippers={len(req.available_shippers)}")

    # Kiểm tra cache
    cache_key = f"matching:{req.order_id}"
    cached = await redis_db.get_key(cache_key)
    if cached:
        logger.info(f"Cache hit for order_id={req.order_id}")
        return MatchingResponse(**json.loads(cached))

    result = matching_service.rank_shippers(req)

    # Lưu cache 2 phút
    await redis_db.set_key(cache_key, result.model_dump_json(), ttl=CACHE_TTL)

    return result
