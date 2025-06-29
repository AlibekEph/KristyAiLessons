"""Lesson model."""

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from .base import Base


class Lesson(Base):
    """Lesson model."""
    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_url = Column(String, nullable=False)
    lesson_type = Column(String, nullable=False)
    student_id = Column(String)
    teacher_id = Column(String)
    status = Column(String, default="pending")
    recording_session_id = Column(String)  # Deprecated, use recall_bot_id
    recall_bot_id = Column(String)  # Bot ID from Recall.ai API
    recording_id = Column(String)  # Recording ID from Recall.ai API (String, not UUID)
    transcript_id = Column(UUID(as_uuid=True))  # Transcript ID from Recall.ai API
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    lesson_metadata = Column(JSON)

    # Relationships
    transcript = relationship("Transcript", back_populates="lesson", uselist=False)
    materials = relationship("Materials", back_populates="lesson", uselist=False) 