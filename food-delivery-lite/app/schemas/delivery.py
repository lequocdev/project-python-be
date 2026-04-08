from pydantic import BaseModel, Field
from enum import Enum


class FoodType(str, Enum):
    FAST_FOOD = "fast_food"
    RESTAURANT = "restaurant"
    GROCERY = "grocery"


class Coordinates(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class DeliveryRequest(BaseModel):
    pickup: Coordinates
    dropoff: Coordinates
    food_type: FoodType
    order_value: float = Field(..., gt=0)
    weight_kg: float = Field(default=1.0, gt=0)


class DeliveryBreakdown(BaseModel):
    base_fee: float
    distance_fee: float
    weight_fee: float
    surge_factor: float


class DeliveryResponse(BaseModel):
    total_fee: float
    currency: str = "VND"
    eta_minutes: int
    breakdown: DeliveryBreakdown
