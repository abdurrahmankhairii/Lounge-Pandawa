"""
Application Configuration — Environment Variables & Settings
Arjuna Smart Lounge App
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_ENV: str = "development"
    APP_NAME: str = "Arjuna Smart Lounge"
    APP_VERSION: str = "2.0.0"
    APP_BASE_URL: str = "http://localhost:3555"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "arjuna_lounge_db"
    DB_USER: str = "arjuna_user"
    DB_PASSWORD: str = "arjuna_dev_password"
    DATABASE_URL: Optional[str] = None

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "")

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production-64-chars-minimum-required!!"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_PRIVATE_KEY_PATH: Optional[str] = None
    JWT_PUBLIC_KEY_PATH: Optional[str] = None

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3555",
        "http://localhost:3001",
        "https://arjunalounge.id",
    ]

    # Midtrans
    MIDTRANS_SERVER_KEY: str = ""
    MIDTRANS_CLIENT_KEY: str = ""
    MIDTRANS_IS_PRODUCTION: bool = False

    # WhatsApp
    WA_API_URL: str = "https://graph.facebook.com/v19.0"
    WA_TOKEN: str = ""
    WA_PHONE_ID: str = ""

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@arjunalounge.id"

    # Sentry
    SENTRY_DSN: Optional[str] = None

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = "arjuna-lounge"

    # Lounge Settings
    LOUNGE_ID: str = "arjuna-vip-01"
    DEFAULT_SLOT_CAPACITY: int = 20
    SLOT_DURATION_MINUTES: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — loaded once per process."""
    return Settings()


settings = get_settings()
