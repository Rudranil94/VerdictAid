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
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: Optional[str] = None
    
    # Redis
    REDIS_URL: str
    MAX_STORED_NOTIFICATIONS: int = 100
    NOTIFICATION_RETENTION_DAYS: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # Email
    SMTP_TLS: bool = True
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM_ADDRESS: str
    EMAIL_FROM_NAME: str
    
    # Push Notifications
    VAPID_PUBLIC_KEY: str
    VAPID_PRIVATE_KEY: str
    VAPID_CLAIMS_EMAIL: str
    FCM_API_KEY: Optional[str] = None
    FCM_PROJECT_ID: Optional[str] = None
    
    # Document Analysis
    OPENAI_API_KEY: Optional[str] = None
    LANGCHAIN_API_KEY: Optional[str] = None
    
    # Testing
    TESTING: bool = False
    
    class Config:
        model_config = SettingsConfigDict(
            env_file=".env.test" if os.getenv("TESTING") else ".env",
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
    return Settings(_env_file=".env.test" if os.getenv("TESTING") else ".env")

settings = get_settings()
