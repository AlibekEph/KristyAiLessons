"""Educational materials model."""

from sqlalchemy import Column, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from .base import Base


class Materials(Base):
    """Educational materials model."""
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)
    original_transcript = Column(Text)
    corrected_transcript = Column(Text)
    summary = Column(Text)
    homework = Column(Text)
    notes = Column(Text)
    key_vocabulary = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    lesson = relationship("Lesson", back_populates="materials") 