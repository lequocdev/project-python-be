from fastapi import FastAPI
from app.api.v1 import delivery, fraud, matching
from app.config import settings

app = FastAPI(
    title="Food Delivery Lite",
    description="Python microservice mô phỏng hệ thống giao đồ ăn",
    version="1.0.0",
)

# Register routers
app.include_router(delivery.router, prefix="/api/v1/delivery", tags=["Delivery"])
app.include_router(fraud.router, prefix="/api/v1/fraud", tags=["Fraud"])
app.include_router(matching.router, prefix="/api/v1/matching", tags=["Matching"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "env": settings.ENV}
