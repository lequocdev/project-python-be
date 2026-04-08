import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app


# ----- Fixtures -----

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ----- Health -----

@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ----- Delivery -----

@pytest.mark.asyncio
@patch("app.api.v1.delivery.mongodb.log_delivery", new_callable=AsyncMock)
async def test_delivery_estimate_success(mock_log, client):
    payload = {
        "pickup": {"lat": 10.776, "lng": 106.700},
        "dropoff": {"lat": 10.800, "lng": 106.720},
        "food_type": "fast_food",
        "order_value": 150000,
        "weight_kg": 1.5,
    }
    response = await client.post("/api/v1/delivery/estimate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "total_fee" in data
    assert "eta_minutes" in data
    assert data["currency"] == "VND"


@pytest.mark.asyncio
@patch("app.api.v1.delivery.mongodb.log_delivery", new_callable=AsyncMock)
async def test_delivery_surge_at_noon(mock_log, client):
    """Surge 1.3 vào giờ trưa (11–13h) – kiểm tra breakdown."""
    from unittest.mock import patch as p
    with p("app.services.delivery_service.datetime") as mock_dt:
        mock_dt.now.return_value.hour = 12
        payload = {
            "pickup": {"lat": 10.776, "lng": 106.700},
            "dropoff": {"lat": 10.790, "lng": 106.710},
            "food_type": "restaurant",
            "order_value": 200000,
            "weight_kg": 1.0,
        }
        response = await client.post("/api/v1/delivery/estimate", json=payload)
    assert response.status_code == 200
    assert response.json()["breakdown"]["surge_factor"] == 1.3


@pytest.mark.asyncio
async def test_invalid_coordinates_422(client):
    payload = {
        "pickup": {"lat": 999, "lng": 106.700},  # lat invalid
        "dropoff": {"lat": 10.800, "lng": 106.720},
        "food_type": "fast_food",
        "order_value": 100000,
    }
    response = await client.post("/api/v1/delivery/estimate", json=payload)
    assert response.status_code == 422


# ----- Fraud -----

@pytest.mark.asyncio
@patch("app.api.v1.fraud.redis_db.increment_counter", new_callable=AsyncMock, return_value=1)
@patch("app.api.v1.fraud.mongodb.log_fraud_check", new_callable=AsyncMock)
async def test_fraud_approved(mock_log, mock_counter, client):
    payload = {
        "user_id": "user_001",
        "order_value": 100000,
        "pickup_lat": 10.776,
        "pickup_lng": 106.700,
        "dropoff_lat": 10.780,
        "dropoff_lng": 106.705,
        "account_age_days": 100,
        "device_id": "device_abc",
    }
    response = await client.post("/api/v1/fraud/evaluate", json=payload)
    assert response.status_code == 200
    assert response.json()["decision"] == "approved"


@pytest.mark.asyncio
@patch("app.api.v1.fraud.redis_db.increment_counter", new_callable=AsyncMock, return_value=1)
@patch("app.api.v1.fraud.mongodb.log_fraud_check", new_callable=AsyncMock)
async def test_fraud_blocked_new_account(mock_log, mock_counter, client):
    payload = {
        "user_id": "user_new",
        "order_value": 6_000_000,   # >5M → score +20
        "pickup_lat": 10.776,
        "pickup_lng": 106.700,
        "dropoff_lat": 10.980,      # xa → score +30
        "dropoff_lng": 106.900,
        "account_age_days": 0,      # mới tạo → score +30
        "device_id": "dev_xyz",
    }
    response = await client.post("/api/v1/fraud/evaluate", json=payload)
    assert response.status_code == 200
    assert response.json()["decision"] == "blocked"


@pytest.mark.asyncio
@patch("app.api.v1.fraud.redis_db.increment_counter", new_callable=AsyncMock, return_value=6)
@patch("app.api.v1.fraud.mongodb.log_fraud_check", new_callable=AsyncMock)
async def test_fraud_velocity_check_redis(mock_log, mock_counter, client):
    """Velocity >5 đơn/giờ → score +40 → blocked."""
    payload = {
        "user_id": "user_spam",
        "order_value": 50000,
        "pickup_lat": 10.776,
        "pickup_lng": 106.700,
        "dropoff_lat": 10.778,
        "dropoff_lng": 106.702,
        "account_age_days": 30,
        "device_id": "dev_spam",
    }
    response = await client.post("/api/v1/fraud/evaluate", json=payload)
    assert response.status_code == 200
    assert response.json()["risk_score"] >= 40


# ----- Matching -----

@pytest.mark.asyncio
@patch("app.api.v1.matching.redis_db.get_key", new_callable=AsyncMock, return_value=None)
@patch("app.api.v1.matching.redis_db.set_key", new_callable=AsyncMock)
async def test_matching_returns_ranked_list(mock_set, mock_get, client):
    payload = {
        "order_id": "order_001",
        "pickup_lat": 10.776,
        "pickup_lng": 106.700,
        "available_shippers": [
            {"shipper_id": "s1", "distance_km": 1.0, "rating": 4.5, "acceptance_rate": 0.9, "completed_orders": 200},
            {"shipper_id": "s2", "distance_km": 3.0, "rating": 4.8, "acceptance_rate": 0.7, "completed_orders": 100},
            {"shipper_id": "s3", "distance_km": 0.5, "rating": 3.5, "acceptance_rate": 0.8, "completed_orders": 50},
        ],
    }
    response = await client.post("/api/v1/matching/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == "order_001"
    assert len(data["ranked_shippers"]) == 3
    assert data["ranked_shippers"][0]["rank"] == 1


@pytest.mark.asyncio
@patch("app.api.v1.matching.redis_db.get_key", new_callable=AsyncMock, return_value=None)
@patch("app.api.v1.matching.redis_db.set_key", new_callable=AsyncMock)
async def test_matching_single_shipper(mock_set, mock_get, client):
    payload = {
        "order_id": "order_002",
        "pickup_lat": 10.776,
        "pickup_lng": 106.700,
        "available_shippers": [
            {"shipper_id": "s_only", "distance_km": 2.0, "rating": 4.0, "acceptance_rate": 0.85, "completed_orders": 75},
        ],
    }
    response = await client.post("/api/v1/matching/score", json=payload)
    assert response.status_code == 200
    assert response.json()["top_shipper_id"] == "s_only"
