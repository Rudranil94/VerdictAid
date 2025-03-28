import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, Any
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base
from app.models.user import User
from app.models.user_device import UserDevice, DeviceType, NotificationChannel
from app.core.redis import get_redis_client, close_redis_connection
import redis.asyncio as redis
import json

# Set test environment
os.environ["TESTING"] = "True"

# Test database
TEST_DATABASE_URL = settings.get_database_url()
engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for the app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="test_hashed_password",
        is_active=True,
        is_superuser=False,
        full_name="Test User"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_devices(db: AsyncSession, test_user: User) -> list[UserDevice]:
    """Create test devices for the user."""
    devices = [
        UserDevice(
            user_id=test_user.id,
            device_type=DeviceType.WEB,
            device_name="Test Browser",
            notification_channel=NotificationChannel.WEB_PUSH,
            push_subscription=json.dumps({
                "endpoint": "https://test.push.services.mozilla.com/test",
                "keys": {
                    "auth": "test_auth",
                    "p256dh": "test_p256dh"
                }
            }),
            is_active=True
        ),
        UserDevice(
            user_id=test_user.id,
            device_type=DeviceType.MOBILE,
            device_name="Test Mobile",
            notification_channel=NotificationChannel.FCM,
            fcm_token="test_fcm_token",
            is_active=True
        ),
        UserDevice(
            user_id=test_user.id,
            device_type=DeviceType.DESKTOP,
            device_name="Test Desktop",
            notification_channel=NotificationChannel.EMAIL,
            is_active=True
        )
    ]
    
    for device in devices:
        db.add(device)
    await db.commit()
    
    for device in devices:
        await db.refresh(device)
    
    return devices

@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Create a Redis client for testing."""
    client = await get_redis_client()
    await client.flushdb()  # Clear test database
    yield client
    await client.flushdb()
    await close_redis_connection()

@pytest.fixture
def test_notification() -> Dict[str, Any]:
    """Create a test notification payload."""
    return {
        "type": "document_processed",
        "data": {
            "document_id": 1,
            "status": "completed",
            "details": {
                "pages": 5,
                "word_count": 1000
            }
        }
    }
