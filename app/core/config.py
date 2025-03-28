from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Project name and version
    PROJECT_NAME: str = "Verdict Aid"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@host:port/dbname")
    TEST_DATABASE_URL: Optional[str] = None
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://host:port")
    MAX_STORED_NOTIFICATIONS: int = 100
    NOTIFICATION_RETENTION_DAYS: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # Email
    SMTP_TLS: bool = True
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "your-email@gmail.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "your-app-specific-password")
    EMAIL_FROM_ADDRESS: str = os.getenv("EMAIL_FROM_ADDRESS", "noreply@example.com")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "Verdict Aid")
    
    # Push Notifications
    VAPID_PUBLIC_KEY: str = os.getenv("VAPID_PUBLIC_KEY", "your-vapid-public-key")
    VAPID_PRIVATE_KEY: str = os.getenv("VAPID_PRIVATE_KEY", "your-vapid-private-key")
    VAPID_CLAIMS_EMAIL: str = os.getenv("VAPID_CLAIMS_EMAIL", "your-email@example.com")
    FCM_API_KEY: Optional[str] = None
    FCM_PROJECT_ID: Optional[str] = None
    
    # Document Analysis
    OPENAI_API_KEY: Optional[str] = None
    LANGCHAIN_API_KEY: Optional[str] = None
    
    # Testing
    TESTING: bool = False
    
    class Config:
        model_config = SettingsConfigDict(
            env_file_encoding="utf-8",
            case_sensitive=True,
            extra="ignore"
        )

    def get_database_url(self) -> str:
        """Get the appropriate database URL based on environment."""
        if self.TESTING and self.TEST_DATABASE_URL:
            return self.TEST_DATABASE_URL
        return self.DATABASE_URL


@lru_cache()
def get_settings() -> Settings:
    """Create cached settings instance."""
    return Settings()
