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
