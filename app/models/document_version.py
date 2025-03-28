from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import TimestampedBase

class DocumentVersion(TimestampedBase):
    __tablename__ = "document_versions"
    
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON)
    changes_summary = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="versions")
    user = relationship("User")
    
    class Config:
        orm_mode = True

class DocumentChange(TimestampedBase):
    __tablename__ = "document_changes"
    
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_from = Column(Integer, nullable=False)
    version_to = Column(Integer, nullable=False)
    change_type = Column(String(50), nullable=False)  # create, update, delete
    changes = Column(JSON)  # Detailed changes in JSON format
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    document = relationship("Document")
    user = relationship("User")
