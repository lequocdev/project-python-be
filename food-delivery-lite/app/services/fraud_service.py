import math
from app.schemas.fraud import FraudDecision, FraudCheckRequest, FraudCheckResponse


def _distance_km(req: FraudCheckRequest) -> float:
    """Tính khoảng cách pickup → dropoff (đơn giản, không Haversine đầy đủ)."""
    dlat = req.dropoff_lat - req.pickup_lat
    dlng = req.dropoff_lng - req.pickup_lng
    return math.sqrt(dlat**2 + dlng**2) * 111  # ~111 km/độ


# Các rule: (condition_fn, score, reason)
RULES = [
    (lambda req, orders_last_hour: orders_last_hour > 5, 40, "Quá nhiều đơn trong 1 giờ"),
    (lambda req, _: req.account_age_days < 1, 30, "Tài khoản mới tạo"),
    (lambda req, _: _distance_km(req) > 20, 30, "Khoảng cách giao hàng bất thường (>20 km)"),
    (lambda req, _: req.order_value > 5_000_000, 20, "Giá trị đơn hàng rất cao (>5M VND)"),
]


def get_decision(score: int) -> FraudDecision:
    if score < 30:
        return FraudDecision.APPROVED
    if score < 60:
        return FraudDecision.REVIEW
    return FraudDecision.BLOCKED


def evaluate_fraud(req: FraudCheckRequest, orders_last_hour: int = 0) -> FraudCheckResponse:
    """Chấm điểm rủi ro đơn hàng."""
    total_score = 0
    reasons: list[str] = []

    for condition_fn, score, reason in RULES:
        if condition_fn(req, orders_last_hour):
            total_score += score
            reasons.append(reason)

    total_score = min(total_score, 100)
    decision = get_decision(total_score)

    return FraudCheckResponse(
        risk_score=total_score,
        decision=decision,
        reasons=reasons,
    )
