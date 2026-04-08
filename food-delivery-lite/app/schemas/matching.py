from pydantic import BaseModel, Field


class Shipper(BaseModel):
    shipper_id: str
    distance_km: float
    rating: float = Field(..., ge=1.0, le=5.0)
    acceptance_rate: float = Field(..., ge=0.0, le=1.0)
    completed_orders: int


class MatchingRequest(BaseModel):
    order_id: str
    pickup_lat: float
    pickup_lng: float
    available_shippers: list[Shipper]


class RankedShipper(BaseModel):
    shipper_id: str
    score: float
    rank: int


class MatchingResponse(BaseModel):
    order_id: str
    ranked_shippers: list[RankedShipper]
    top_shipper_id: str
