"""
SignAsili Configuration Settings
"""
from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App Info
    APP_NAME: str = "SignAsili"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://signasili:password@localhost:5432/signasili"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 50

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Password Policy
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "https://signasili.org",
        "https://app.signasili.org",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # If not JSON, split by comma
                return [origin.strip() for origin in v.split(",")]
        return v
    
    # Email
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "support@signasili.org"
    
    # SMS (Africa's Talking)
    AT_API_KEY: Optional[str] = None
    AT_USERNAME: Optional[str] = None
    
    # M-PESA (Daraja API)
    MPESA_CONSUMER_KEY: Optional[str] = None
    MPESA_CONSUMER_SECRET: Optional[str] = None
    MPESA_PASSKEY: Optional[str] = None
    MPESA_SHORTCODE: Optional[str] = None
    
    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_STORAGE_BUCKET_NAME: str = "signasili-videos"
    AWS_S3_REGION: str = "eu-west-1"
    
    # Sentry
    SENTRY_DSN: Optional[str] = None
    
    # ML Models
    MODEL_PATH: str = "/app/models"
    SIGN_DETECTION_MODEL: str = "sign_detection.tflite"
    LIP_SYNC_MODEL: str = "lip_sync.tflite"
    TRANSLATION_MODEL: str = "translator.tflite"
    
    # Offline Packs
    OFFLINE_PACK_PATH: str = "/tmp/offline_packs"
    MAX_OFFLINE_PACK_SIZE_MB: int = 50
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    AUTH_RATE_LIMIT: int = 5
    AUTH_RATE_LIMIT_WINDOW: int = 900  # 15 minutes
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Feature Flags
    FEATURE_BRIDGE_PROGRAMME: bool = True
    FEATURE_AI_COACH: bool = True
    FEATURE_COMMUNITY_CIRCLES: bool = False
    
    # Timezone
    TIMEZONE: str = "Africa/Nairobi"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
