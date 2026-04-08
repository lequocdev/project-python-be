from pydantic import BaseModel, Field
from enum import Enum


class FraudDecision(str, Enum):
    APPROVED = "approved"   # score 0–29
    REVIEW = "review"       # score 30–59
    BLOCKED = "blocked"     # score 60–100


class FraudCheckRequest(BaseModel):
    user_id: str
    order_value: float
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    account_age_days: int
    device_id: str


class FraudCheckResponse(BaseModel):
    risk_score: int = Field(..., ge=0, le=100)
    decision: FraudDecision
    reasons: list[str]
