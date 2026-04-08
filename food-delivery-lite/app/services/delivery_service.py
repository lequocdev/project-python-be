import math
from datetime import datetime


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Tính khoảng cách (km) giữa 2 tọa độ theo công thức Haversine."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_surge_factor(hour: int) -> float:
    """Hệ số surge theo giờ trong ngày."""
    if hour in range(11, 14):
        return 1.3   # giờ trưa
    if hour in range(17, 20):
        return 1.5   # giờ tối
    return 1.0


def calculate_fee(distance_km: float, weight_kg: float, order_value: float, hour: int) -> dict:
    """Tính phí giao hàng (VND)."""
    base_fee = 15_000
    distance_fee = distance_km * 5_000
    weight_fee = max(0.0, (weight_kg - 1) * 2_000)
    surge = get_surge_factor(hour)
    total = (base_fee + distance_fee + weight_fee) * surge
    return {
        "total": round(total, 2),
        "base_fee": round(base_fee * surge, 2),
        "distance_fee": round(distance_fee * surge, 2),
        "weight_fee": round(weight_fee * surge, 2),
        "surge_factor": surge,
    }


def calculate_eta(distance_km: float) -> int:
    """Ước tính thời gian giao hàng (phút)."""
    avg_speed_kmh = 25
    return int((distance_km / avg_speed_kmh) * 60) + 5  # +5 phút chuẩn bị đơn


def estimate_delivery(
    pickup_lat: float,
    pickup_lng: float,
    dropoff_lat: float,
    dropoff_lng: float,
    weight_kg: float,
    order_value: float,
) -> dict:
    """Entry point cho delivery endpoint."""
    now_hour = datetime.now().hour
    distance_km = _haversine_km(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)
    fee_info = calculate_fee(distance_km, weight_kg, order_value, now_hour)
    eta = calculate_eta(distance_km)
    return {
        "total_fee": fee_info["total"],
        "eta_minutes": eta,
        "breakdown": {
            "base_fee": fee_info["base_fee"],
            "distance_fee": fee_info["distance_fee"],
            "weight_fee": fee_info["weight_fee"],
            "surge_factor": fee_info["surge_factor"],
        },
    }
