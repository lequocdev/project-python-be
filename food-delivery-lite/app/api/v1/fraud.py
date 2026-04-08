from fastapi import APIRouter
from app.schemas.fraud import FraudCheckRequest, FraudCheckResponse
from app.services import fraud_service
from app.database import redis as redis_db, mongodb
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

VELOCITY_TTL = 3600  # 1 giờ


@router.post("/evaluate", response_model=FraudCheckResponse)
async def evaluate_fraud(req: FraudCheckRequest):
    """POST /api/v1/fraud/evaluate – Chấm điểm rủi ro đơn hàng."""
    logger.info(f"Fraud evaluate: user_id={req.user_id}, order_value={req.order_value}")

    # Velocity check: đếm số đơn trong 1 giờ qua
    velocity_key = f"orders:{req.user_id}:count"
    orders_last_hour = await redis_db.increment_counter(velocity_key, ttl=VELOCITY_TTL)

    result = fraud_service.evaluate_fraud(req, orders_last_hour=orders_last_hour)

    # Log vào MongoDB
    await mongodb.log_fraud_check({
        "user_id": req.user_id,
        "order_value": req.order_value,
        "risk_score": result.risk_score,
        "decision": result.decision,
        "reasons": result.reasons,
    })

    return result
