# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Social Media Manager"
    APP_VERSION: str = "2.0.0"
    ENV: str = "development"
    DEBUG: bool = True

    RATE_LIMIT_PER_MINUTE: int = 10
    
    # Database
    DATABASE_URL: str

    # Redis (for Celery)
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # API keys for Instagram, Twitter (X), TikTok
    INSTAGRAM_CLIENT_ID: str | None = None
    INSTAGRAM_CLIENT_SECRET: str | None = None
    TWITTER_API_KEY: str | None = None
    TWITTER_API_SECRET: str | None = None
    TIKTOK_CLIENT_KEY: str | None = None
    TIKTOK_CLIENT_SECRET: str | None = None

    class Config:
        env_file = ".env"   

settings = Settings()
