from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import TimestampedBase

class UserActivity(TimestampedBase):
    __tablename__ = "user_activities"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer)
    action = Column(String(50), nullable=False)
    metadata = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    
    # Relationships
    user = relationship("User", back_populates="activities")
    
    class Config:
        orm_mode = True

class AuditLog(TimestampedBase):
    __tablename__ = "audit_logs"
    
    user_id = Column(Integer, ForeignKey("users.id"))
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(String(500), nullable=False)
    metadata = Column(JSON)
    source_ip = Column(String(50))
    
    # Relationships
    user = relationship("User")
