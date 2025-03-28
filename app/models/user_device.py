from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime
import enum
from typing import Optional

class DeviceType(str, enum.Enum):
    WEB = "web"
    MOBILE = "mobile"
    DESKTOP = "desktop"

class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    WEB_PUSH = "web_push"
    FCM = "fcm"

class UserDevice(Base):
    __tablename__ = "user_devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_type = Column(Enum(DeviceType), nullable=False)
    notification_channel = Column(Enum(NotificationChannel), nullable=False)
    device_name = Column(String, nullable=True)
    push_subscription = Column(String, nullable=True)  # Web Push subscription
    fcm_token = Column(String, nullable=True)  # FCM token
    is_active = Column(Boolean, default=True)
    last_active = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="devices")

    class Config:
        orm_mode = True
