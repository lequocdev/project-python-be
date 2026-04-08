---
name: food-delivery-lite
description: >
  Hướng dẫn xây dựng dự án thực hành "Food Delivery Lite" – một Python microservice
  mô phỏng hệ thống giao đồ ăn, có cấu trúc thư mục y hệt ai-lite-service để luyện
  FastAPI, Pydantic v2, Redis, và MongoDB. Sử dụng skill này bất cứ khi nào cần tạo
  file, scaffold cấu trúc thư mục, viết code mẫu, hoặc giải thích bất kỳ phần nào
  của dự án Food Delivery Lite.
---

# Food Delivery Lite – Skill

Dự án thực hành mô phỏng **ai-lite-service** với bài toán giao đồ ăn.  
Mục tiêu: luyện FastAPI + Pydantic v2 + Redis + MongoDB đúng chuẩn layered architecture.

---

## Cấu trúc thư mục

```
food-delivery-lite/
├── app/
│   ├── main.py                  # Khởi động FastAPI, đăng ký routers
│   ├── config.py                # Pydantic BaseSettings, đọc .env
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── delivery.py      # POST /api/v1/delivery/estimate
│   │       ├── fraud.py         # POST /api/v1/fraud/evaluate
│   │       └── matching.py      # POST /api/v1/matching/score
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── delivery.py          # DeliveryRequest, DeliveryResponse
│   │   ├── fraud.py             # FraudCheckRequest, FraudCheckResponse
│   │   └── matching.py          # MatchingRequest, MatchingResponse
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── delivery_service.py  # Tính phí, ETA, surge – pure functions
│   │   ├── fraud_service.py     # Risk scoring logic
│   │   └── matching_service.py  # Weighted score cho shipper
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── redis.py             # Redis client, helpers
│   │   └── mongodb.py           # MongoDB client, collection helpers
│   │
│   └── utils/
│       ├── __init__.py
│       └── logger.py            # Structured logger wrapper
│
├── tests/
│   ├── __init__.py
│   └── test_api.py              # pytest + HTTPX TestClient
│
├── .env                         # Biến môi trường local
├── .env.example                 # Mẫu .env để commit lên git
├── requirements.txt
└── README.md
```

---

## Nguyên tắc layering (BẮT BUỘC tuân theo)

```
Request
  → api/v1/       (HTTP only: parse input, gọi service, trả response)
      → services/ (Business logic: tính toán, rules – pure functions)
          → database/     (Redis cache, MongoDB log)
          → (tương lai) integrations/
  → schemas/      (Pydantic validate mọi input/output)
```

- `api/v1/` **KHÔNG** chứa logic tính toán
- `services/` **KHÔNG** import FastAPI, không biết về HTTP
- `database/` **KHÔNG** chứa business logic

---

## Chi tiết từng module

### `app/config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_PORT: int = 8000
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    REDIS_URL: str = "redis://localhost:6379"
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "food_delivery_lite"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

### `app/schemas/delivery.py`
```python
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
```

---

### `app/schemas/fraud.py`
```python
from pydantic import BaseModel, Field
from enum import Enum

class FraudDecision(str, Enum):
    APPROVED = "approved"       # score 0–29
    REVIEW = "review"           # score 30–59
    BLOCKED = "blocked"         # score 60–100

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
```

---

### `app/schemas/matching.py`
```python
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
```

---

### `app/services/delivery_service.py`
Logic cần implement (pure functions):

```python
# Công thức tính fee
def calculate_fee(distance_km, weight_kg, order_value, hour) -> dict:
    base_fee = 15_000
    distance_fee = distance_km * 5_000
    weight_fee = max(0, (weight_kg - 1) * 2_000)
    surge = get_surge_factor(hour)
    total = (base_fee + distance_fee + weight_fee) * surge
    return {"total": total, "surge_factor": surge, ...}

# Hệ số surge theo giờ
def get_surge_factor(hour: int) -> float:
    if hour in range(11, 14):   return 1.3   # giờ trưa
    if hour in range(17, 20):   return 1.5   # giờ tối
    return 1.0

# Tính ETA (phút)
def calculate_eta(distance_km: float) -> int:
    avg_speed_kmh = 25
    return int((distance_km / avg_speed_kmh) * 60) + 5  # +5 chuẩn bị đơn
```

---

### `app/services/fraud_service.py`
Logic cần implement:

```python
# Các rule chấm điểm
RULES = [
    # (condition_fn, score, reason)
    (lambda req, orders_last_hour: orders_last_hour > 5,  40, "Quá nhiều đơn trong 1 giờ"),
    (lambda req, _: req.account_age_days < 1,             30, "Tài khoản mới tạo"),
    (lambda req, _: _distance(req) > 20,                  30, "Khoảng cách bất thường"),
]

# Decision theo score
def get_decision(score: int) -> FraudDecision:
    if score < 30:   return FraudDecision.APPROVED
    if score < 60:   return FraudDecision.REVIEW
    return FraudDecision.BLOCKED
```

Redis dùng để: đếm số đơn trong 1 giờ qua theo `user_id`.

---

### `app/services/matching_service.py`
Logic cần implement:

```python
# Trọng số
WEIGHTS = {
    "distance":        0.40,
    "rating":          0.35,
    "acceptance_rate": 0.25,
}

def score_shipper(shipper: Shipper) -> float:
    # Normalize từng yếu tố về 0–1 trước khi nhân trọng số
    distance_score    = 1 / (1 + shipper.distance_km)
    rating_score      = (shipper.rating - 1) / 4
    acceptance_score  = shipper.acceptance_rate
    return (
        distance_score    * WEIGHTS["distance"] +
        rating_score      * WEIGHTS["rating"] +
        acceptance_score  * WEIGHTS["acceptance_rate"]
    )
```

---

### `app/database/redis.py`
Cần implement:
- `get_redis_client()` – connection pool, singleton
- `get_key(key)` / `set_key(key, value, ttl)`
- `increment_counter(key, ttl)` – dùng cho velocity check

### `app/database/mongodb.py`
Cần implement:
- `get_db()` – Motor async client
- `log_fraud_check(data)` – insert vào collection `fraud_logs`
- `log_delivery(data)` – insert vào collection `delivery_logs`

---

## Endpoints

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/health` | Health check |
| POST | `/api/v1/delivery/estimate` | Tính phí + ETA |
| POST | `/api/v1/fraud/evaluate` | Chấm điểm rủi ro đơn hàng |
| POST | `/api/v1/matching/score` | Xếp hạng shipper |

---

## Redis patterns cần luyện

| Pattern | Dùng ở đâu | TTL |
|---------|-----------|-----|
| Cache delivery fee | `delivery:{hash_input}` | 5 phút |
| Velocity counter | `orders:{user_id}:count` | 1 giờ |
| Cache matching result | `matching:{order_id}` | 2 phút |

---

## Thứ tự viết code (khuyến nghị)

```
1. config.py + .env
2. schemas/ (tất cả 3 file)
3. utils/logger.py
4. database/redis.py + database/mongodb.py
5. services/delivery_service.py
6. services/fraud_service.py
7. services/matching_service.py
8. api/v1/delivery.py → fraud.py → matching.py
9. main.py (đăng ký router)
10. tests/test_api.py
```

---

## Test cases cần viết

```python
# Happy path
test_delivery_estimate_success()
test_fraud_approved()
test_fraud_blocked_new_account()
test_matching_returns_ranked_list()

# Edge cases
test_delivery_surge_at_noon()
test_fraud_velocity_check_redis()
test_matching_single_shipper()
test_invalid_coordinates_422()
```

---

## .env.example

```
APP_PORT=8000
ENV=development
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=food_delivery_lite
```

---

## requirements.txt

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
redis>=5.0.0
motor>=3.4.0          # async MongoDB driver
httpx>=0.27.0         # dùng cho TestClient trong tests
pytest>=8.0.0
pytest-asyncio>=0.23.0
python-dotenv>=1.0.0
```

---

## Mapping sang ai-lite-service

| Food Delivery Lite | ai-lite-service |
|-------------------|----------------|
| `delivery_service.py` | `pricing_service.py` |
| `fraud_service.py` | `fraud_service.py` |
| `matching_service.py` | `matching_service.py` |
| Velocity check (đơn/giờ) | Velocity check (chuyến/giờ) |
| Surge theo giờ trưa/tối | Surge theo giờ cao điểm |
| Shipper weighted score | Driver weighted score |

Khi chuyển sang ai-lite-service thật:
- **Giữ nguyên**: cấu trúc thư mục, layering, Redis patterns, MongoDB logging
- **Thay thế**: business logic trong `services/`, schemas input/output