# Food Delivery Lite

Python microservice mô phỏng hệ thống giao đồ ăn, xây dựng theo chuẩn **layered architecture** với FastAPI + Pydantic v2 + Redis + MongoDB.

---

## Mục tiêu

Dự án thực hành luyện các kỹ năng:
- FastAPI (async endpoints, Pydantic validation)
- Pydantic v2 (BaseModel, BaseSettings, Field validators)
- Redis (caching, velocity counter)
- MongoDB / Motor (async logging)
- Layered architecture (api → service → database)

---

## Cấu trúc thư mục

```
food-delivery-lite/
├── app/
│   ├── main.py                  # Khởi động FastAPI, đăng ký routers
│   ├── config.py                # Pydantic BaseSettings, đọc .env
│   ├── api/v1/
│   │   ├── delivery.py          # POST /api/v1/delivery/estimate
│   │   ├── fraud.py             # POST /api/v1/fraud/evaluate
│   │   └── matching.py          # POST /api/v1/matching/score
│   ├── schemas/
│   │   ├── delivery.py
│   │   ├── fraud.py
│   │   └── matching.py
│   ├── services/
│   │   ├── delivery_service.py
│   │   ├── fraud_service.py
│   │   └── matching_service.py
│   ├── database/
│   │   ├── redis.py
│   │   └── mongodb.py
│   └── utils/
│       └── logger.py
├── tests/
│   └── test_api.py
├── .env
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Cài đặt & Chạy

```bash
# 1. Tạo virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Copy .env
copy .env.example .env

# 4. Chạy server
uvicorn app.main:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs

---

## Endpoints

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/health` | Health check |
| POST | `/api/v1/delivery/estimate` | Tính phí + ETA |
| POST | `/api/v1/fraud/evaluate` | Chấm điểm rủi ro đơn hàng |
| POST | `/api/v1/matching/score` | Xếp hạng shipper |

---

## Chạy Tests

```bash
pytest -v
```

---

## Redis Patterns

| Pattern | Key | TTL |
|---------|-----|-----|
| Cache delivery fee | `delivery:{hash}` | 5 phút |
| Velocity counter | `orders:{user_id}:count` | 1 giờ |
| Cache matching result | `matching:{order_id}` | 2 phút |
