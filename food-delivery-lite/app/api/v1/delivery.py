from fastapi import APIRouter
from app.schemas.delivery import DeliveryRequest, DeliveryResponse
from app.services import delivery_service
from app.database import mongodb
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/estimate", response_model=DeliveryResponse)
async def estimate_delivery(req: DeliveryRequest):
    """POST /api/v1/delivery/estimate – Tính phí giao hàng và ETA."""
    logger.info(f"Delivery estimate request: pickup={req.pickup}, dropoff={req.dropoff}")

    result = delivery_service.estimate_delivery(
        pickup_lat=req.pickup.lat,
        pickup_lng=req.pickup.lng,
        dropoff_lat=req.dropoff.lat,
        dropoff_lng=req.dropoff.lng,
        weight_kg=req.weight_kg,
        order_value=req.order_value,
    )

    # Log vào MongoDB (không block response)
    await mongodb.log_delivery({
        "pickup": req.pickup.model_dump(),
        "dropoff": req.dropoff.model_dump(),
        "food_type": req.food_type,
        "order_value": req.order_value,
        "weight_kg": req.weight_kg,
        **result,
    })

    return DeliveryResponse(
        total_fee=result["total_fee"],
        eta_minutes=result["eta_minutes"],
        breakdown=result["breakdown"],
    )
