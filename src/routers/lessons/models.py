"""Pydantic models for lesson-related requests and responses"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class RecordLessonRequest(BaseModel):
    """Запрос на запись урока"""
    meeting_url: str = Field(
        ...,
        description="URL встречи (Zoom, Google Meet и т.д.)",
        example="https://zoom.us/j/1234567890"
    )
    lesson_type: str = Field(
        ...,
        description="Тип урока",
        example="chinese",
        pattern="^(chinese|english)$"
    )
    student_id: Optional[str] = Field(
        None,
        description="ID студента",
        example="student_123"
    )
    teacher_id: Optional[str] = Field(
        None,
        description="ID преподавателя",
        example="teacher_456"
    )
    student_level: Optional[str] = Field(
        None,
        description="Уровень студента",
        example="beginner",
        pattern="^(beginner|intermediate|advanced)$"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Дополнительные метаданные",
        example={"topic": "Числа от 1 до 10", "lesson_number": 5}
    )

    class Config:
        json_schema_extra = {
            "example": {
                "meeting_url": "https://zoom.us/j/1234567890",
                "lesson_type": "chinese",
                "student_id": "student_123",
                "student_level": "beginner",
                "metadata": {
                    "topic": "Базовые приветствия",
                    "lesson_number": 1
                }
            }
        }


class LessonResponse(BaseModel):
    """Информация об уроке"""
    id: uuid.UUID = Field(..., description="Уникальный ID урока")
    status: str = Field(
        ...,
        description="Статус обработки урока",
        example="recording",
        pattern="^(pending|recording|transcribing|processing|completed|failed)$"
    )
    meeting_url: str = Field(..., description="URL встречи", example="https://zoom.us/j/1234567890")
    lesson_type: str = Field(..., description="Тип урока", example="chinese")
    created_at: datetime = Field(..., description="Время создания записи")
    transcript_available: bool = Field(False, description="Доступна ли транскрипция")
    materials_available: bool = Field(False, description="Доступны ли учебные материалы")

    class Config:
        from_attributes = True


class ProcessLessonRequest(BaseModel):
    """Запрос на проверку статуса урока"""
    lesson_id: uuid.UUID = Field(..., description="ID урока для проверки статуса") 