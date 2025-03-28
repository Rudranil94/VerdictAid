import pytest
import json
from typing import Dict, Any, List
from fastapi import WebSocket
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.user_device import UserDevice
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService
from app.services.push_service import PushService
import redis.asyncio as redis

pytestmark = pytest.mark.asyncio

async def test_notification_manager_connect(
    test_user: User,
    redis_client: redis.Redis
):
    """Test WebSocket connection management."""
    notification_service = NotificationService()
    
    # Create a mock WebSocket
    class MockWebSocket:
        async def accept(self):
            pass
        async def send_json(self, data: Dict[str, Any]):
            pass
        async def close(self):
            pass
    
    websocket = MockWebSocket()
    
    # Test connection
    await notification_service.manager.connect(websocket, test_user.id)
    assert test_user.id in notification_service.manager.active_connections
    assert websocket in notification_service.manager.active_connections[test_user.id]
    
    # Test disconnection
    await notification_service.manager.disconnect(websocket, test_user.id)
    assert test_user.id not in notification_service.manager.active_connections

async def test_notification_persistence(
    test_user: User,
    redis_client: redis.Redis,
    test_notification: Dict[str, Any]
):
    """Test notification storage in Redis."""
    notification_service = NotificationService()
    
    # Send notification
    notification_id = await notification_service.manager.send_notification(
        test_user.id,
        test_notification
    )
    
    assert notification_id is not None
    
    # Get pending notifications
    notifications = await notification_service.manager.get_pending_notifications(test_user.id)
    assert len(notifications) == 1
    assert notifications[0]["data"] == test_notification

async def test_email_notification(
    test_user: User,
    test_devices: List[UserDevice],
    test_notification: Dict[str, Any]
):
    """Test email notification delivery."""
    email_service = EmailService()
    
    # Get email device
    email_device = next(
        device for device in test_devices
        if device.notification_channel == "email"
    )
    
    # Send notification
    result = await email_service.send_notification_email(
        to_email=test_user.email,
        notification_type=test_notification["type"],
        notification_data=test_notification["data"]
    )
    
    assert result is True

async def test_push_notification(
    test_user: User,
    test_devices: List[UserDevice],
    test_notification: Dict[str, Any]
):
    """Test push notification delivery."""
    push_service = PushService()
    
    # Test Web Push
    web_device = next(
        device for device in test_devices
        if device.notification_channel == "web_push"
    )
    
    web_result = await push_service.send_notification(
        notification_type=test_notification["type"],
        subscription=json.loads(web_device.push_subscription),
        channel="web_push",
        data=test_notification["data"]
    )
    
    assert web_result is True
    
    # Test FCM
    fcm_device = next(
        device for device in test_devices
        if device.notification_channel == "fcm"
    )
    
    fcm_result = await push_service.send_notification(
        notification_type=test_notification["type"],
        subscription={"token": fcm_device.fcm_token},
        channel="fcm",
        data=test_notification["data"]
    )
    
    assert fcm_result is True

async def test_multi_channel_notification(
    test_user: User,
    test_devices: List[UserDevice],
    test_notification: Dict[str, Any],
    db: AsyncSession
):
    """Test notification delivery through multiple channels."""
    notification_service = NotificationService()
    
    # Send notification through all channels
    notification_id = await notification_service.send_notification(
        user_id=test_user.id,
        notification_type=test_notification["type"],
        data=test_notification["data"],
        db=db
    )
    
    assert notification_id is not None
    
    # Verify notification was stored
    notifications = await notification_service.manager.get_pending_notifications(test_user.id)
    assert len(notifications) == 1
    assert notifications[0]["data"] == test_notification

async def test_notification_expiry(
    test_user: User,
    redis_client: redis.Redis,
    test_notification: Dict[str, Any]
):
    """Test notification expiry in Redis."""
    notification_service = NotificationService()
    
    # Send notification
    notification_id = await notification_service.manager.send_notification(
        test_user.id,
        test_notification
    )
    
    assert notification_id is not None
    
    # Verify TTL is set
    notification_key = f"notifications:{test_user.id}"
    ttl = await redis_client.ttl(notification_key)
    assert ttl > 0

async def test_notification_limit(
    test_user: User,
    redis_client: redis.Redis,
    test_notification: Dict[str, Any]
):
    """Test notification storage limit in Redis."""
    notification_service = NotificationService()
    
    # Send multiple notifications
    for i in range(150):  # More than MAX_STORED_NOTIFICATIONS
        notification = {
            **test_notification,
            "data": {**test_notification["data"], "index": i}
        }
        await notification_service.manager.send_notification(
            test_user.id,
            notification
        )
    
    # Verify only MAX_STORED_NOTIFICATIONS are kept
    notifications = await notification_service.manager.get_pending_notifications(test_user.id)
    assert len(notifications) == 100  # MAX_STORED_NOTIFICATIONS
