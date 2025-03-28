from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime, timedelta
from fastapi import WebSocket
from app.core.redis import get_redis_client
from app.models.user import User
from app.models.user_device import UserDevice
from app.core.config import settings
from app.services.email_service import email_service
from app.services.push_service import push_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Configure logging
logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self._redis = None

    @property
    async def redis(self):
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected. Active connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket, user_id: int):
        self.active_connections[user_id].remove(websocket)
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected. Active connections: {len(self.active_connections)}")

    async def send_notification(self, user_id: int, message: Dict[str, Any]):
        # Store notification in Redis
        try:
            notification_id = await self._store_notification(user_id, message)
            message["id"] = notification_id
            
            # Send to all active WebSocket connections
            if user_id in self.active_connections:
                for connection in self.active_connections[user_id]:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"Failed to send WebSocket message: {str(e)}")
                        continue
            
            return notification_id
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return None

    async def _store_notification(self, user_id: int, message: Dict[str, Any]) -> str:
        try:
            redis_client = await self.redis
            notification_key = f"notifications:{user_id}"
            notification_id = f"{user_id}:{datetime.utcnow().timestamp()}"
            
            # Store notification with TTL
            notification_data = {
                "id": notification_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": message
            }
            
            # Add to user's notification list
            await redis_client.lpush(notification_key, json.dumps(notification_data))
            
            # Trim list to max size
            await redis_client.ltrim(notification_key, 0, settings.MAX_STORED_NOTIFICATIONS - 1)
            
            # Set TTL
            await redis_client.expire(
                notification_key,
                timedelta(days=settings.NOTIFICATION_RETENTION_DAYS).total_seconds()
            )
            
            return notification_id
        except Exception as e:
            logger.error(f"Failed to store notification: {str(e)}")
            raise

    async def get_pending_notifications(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            redis_client = await self.redis
            notification_key = f"notifications:{user_id}"
            notifications = await redis_client.lrange(notification_key, 0, limit - 1)
            return [json.loads(n) for n in notifications]
        except Exception as e:
            logger.error(f"Failed to get pending notifications: {str(e)}")
            return []

class NotificationService:
    def __init__(self):
        self.manager = NotificationManager()
        self._redis = None

    @property
    async def redis(self):
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis

    async def send_notification(
        self,
        user_id: int,
        notification_type: str,
        data: Dict[str, Any],
        db: AsyncSession
    ):
        """Send notification to a user through all configured channels."""
        message = {
            "type": notification_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

        # Send through WebSocket
        notification_id = await self.manager.send_notification(user_id, message)

        try:
            # Get user's devices and preferences
            devices = await self._get_user_devices(user_id, db)
            
            # Send through configured channels
            for device in devices:
                if device.notification_channel == "email":
                    await self._send_email_notification(device, message)
                elif device.notification_channel == "web_push":
                    await self._send_web_push_notification(device, message)
                elif device.notification_channel == "fcm":
                    await self._send_fcm_notification(device, message)

        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return None

        return notification_id

    async def _get_user_devices(self, user_id: int, db: AsyncSession) -> List[UserDevice]:
        """Get user's registered devices."""
        query = (
            select(UserDevice)
            .options(selectinload(UserDevice.user))
            .filter(UserDevice.user_id == user_id)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def _send_email_notification(self, device: UserDevice, message: Dict[str, Any]):
        """Send email notification."""
        if not device.user.email:
            return

        notification_type = message["type"]
        notification_data = message["data"]

        await email_service.send_notification_email(
            to_email=device.user.email,
            notification_type=notification_type,
            notification_data=notification_data
        )

    async def _send_web_push_notification(self, device: UserDevice, message: Dict[str, Any]):
        """Send web push notification."""
        if not device.push_subscription:
            return

        await push_service.send_notification(
            notification_type=message["type"],
            subscription=json.loads(device.push_subscription),
            channel="web_push",
            data=message["data"]
        )

    async def _send_fcm_notification(self, device: UserDevice, message: Dict[str, Any]):
        """Send FCM notification."""
        if not device.fcm_token:
            return

        await push_service.send_notification(
            notification_type=message["type"],
            subscription={"token": device.fcm_token},
            channel="fcm",
            data=message["data"]
        )

notification_service = NotificationService()
