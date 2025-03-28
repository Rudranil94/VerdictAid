from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import TimestampedBase

class Document(TimestampedBase):
    __tablename__ = "documents"
    
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    document_type = Column(String(50), nullable=False)  # contract, nda, legal_notice, etc.
    language = Column(String(5), nullable=False)  # en, es, fr, etc.
    simplified_content = Column(Text)
    analysis_summary = Column(Text)
    risk_assessment = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", back_populates="documents")
