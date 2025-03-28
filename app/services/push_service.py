from typing import Dict, Any, Optional
import json
import logging
import aiohttp
from pywebpush import webpush
from firebase_admin import messaging, initialize_app, credentials
from app.core.config import settings

logger = logging.getLogger(__name__)

class PushService:
    def __init__(self):
        self.vapid_claims = {
            "sub": f"mailto:{settings.VAPID_CLAIMS_EMAIL}"
        }
        
        # Initialize Firebase Admin SDK if FCM is configured
        if settings.FCM_API_KEY and settings.FCM_PROJECT_ID:
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": settings.FCM_PROJECT_ID,
                "private_key": settings.FCM_API_KEY.replace('\\n', '\n'),
                "client_email": settings.VAPID_CLAIMS_EMAIL
            })
            initialize_app(cred)

    async def send_web_push(
        self,
        subscription_info: Dict[str, Any],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        icon: Optional[str] = None,
        click_action: Optional[str] = None
    ) -> bool:
        """Send Web Push notification."""
        try:
            payload = {
                "notification": {
                    "title": title,
                    "body": body,
                    "icon": icon,
                    "click_action": click_action,
                    "data": data or {}
                }
            }

            response = webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims=self.vapid_claims
            )

            logger.info(f"Web Push sent successfully: {response.status_code}")
            return True

        except Exception as e:
            logger.error(f"Web Push failed: {str(e)}")
            return False

    async def send_fcm(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send Firebase Cloud Messaging (FCM) notification."""
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=token
            )

            response = messaging.send(message)
            logger.info(f"FCM sent successfully: {response}")
            return True

        except Exception as e:
            logger.error(f"FCM failed: {str(e)}")
            return False

    async def send_notification(
        self,
        notification_type: str,
        subscription: Dict[str, Any],
        channel: str,
        data: Dict[str, Any]
    ) -> bool:
        """Send a notification through the specified channel."""
        try:
            title = data.get("title", "New Notification")
            body = data.get("body", "You have a new notification")

            if channel == "web_push":
                return await self.send_web_push(
                    subscription_info=subscription,
                    title=title,
                    body=body,
                    data=data
                )
            elif channel == "fcm":
                return await self.send_fcm(
                    token=subscription["token"],
                    title=title,
                    body=body,
                    data=data
                )
            else:
                logger.error(f"Unknown push channel: {channel}")
                return False

        except Exception as e:
            logger.error(f"Failed to send {channel} notification: {str(e)}")
            return False

push_service = PushService()
