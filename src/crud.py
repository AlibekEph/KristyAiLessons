"""CRUD operations for the database."""

import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from .models import Lesson, Transcript, Materials
from .controllers import LessonController
from .filters import LessonFilterParams
from . import schemas

# Legacy CRUD functions for backward compatibility
def get_lesson(db: Session, lesson_id: uuid.UUID):
    """Get lesson by ID."""
    controller = LessonController(db)
    return controller.get_lesson_by_id(lesson_id)

def get_lessons(db: Session, skip: int = 0, limit: int = 100):
    """Get lessons with offset and limit (legacy)."""
    page = (skip // limit) + 1
    controller = LessonController(db)
    lessons, _ = controller.get_lessons_with_pagination(
        page=page,
        page_size=limit
    )
    return lessons

def create_lesson(db: Session, lesson: schemas.LessonCreate):
    """Create a new lesson."""
    controller = LessonController(db)
    return controller.create_lesson(lesson)

# New CRUD functions using controllers
def get_lessons_with_pagination(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    filters: Optional[LessonFilterParams] = None,
    order_by: str = "created_at",
    order_direction: str = "desc"
) -> Tuple[List[Lesson], int]:
    """Get lessons with pagination and filtering."""
    controller = LessonController(db)
    return controller.get_lessons_with_pagination(
        page=page,
        page_size=page_size,
        filters=filters,
        order_by=order_by,
        order_direction=order_direction
    )

def get_lessons_statistics(
    db: Session,
    filters: Optional[LessonFilterParams] = None
) -> dict:
    """Get lessons statistics."""
    controller = LessonController(db)
    return controller.get_lessons_statistics(filters)

def update_lesson_status(db: Session, lesson_id: uuid.UUID, status: str):
    """Update lesson status."""
    controller = LessonController(db)
    return controller.update_lesson_status(lesson_id, status)

def update_lesson(db: Session, lesson_id: uuid.UUID, lesson_data: dict):
    """Update lesson with new data."""
    controller = LessonController(db)
    return controller.update_lesson(lesson_id, lesson_data)

def delete_lesson(db: Session, lesson_id: uuid.UUID) -> bool:
    """Delete a lesson."""
    controller = LessonController(db)
    return controller.delete_lesson(lesson_id)

# Transcript CRUD
def create_lesson_transcript(db: Session, transcript: schemas.TranscriptCreate, lesson_id: uuid.UUID):
    """Create transcript for a lesson."""
    transcript_data = transcript.dict()
    
    # If custom ID is provided, use it
    if transcript_data.get('id'):
        transcript_id = transcript_data.pop('id')
    else:
        transcript_id = uuid.uuid4()
    
    db_transcript = Transcript(id=transcript_id, lesson_id=lesson_id, **transcript_data)
    db.add(db_transcript)
    db.commit()
    db.refresh(db_transcript)
    return db_transcript

def get_lesson_transcript(db: Session, lesson_id: uuid.UUID):
    """Get transcript for a lesson."""
    return db.query(Transcript).filter(Transcript.lesson_id == lesson_id).first()

# Materials CRUD
def create_lesson_materials(db: Session, materials: schemas.MaterialsCreate, lesson_id: uuid.UUID):
    """Create materials for a lesson."""
    db_materials = Materials(**materials.dict(), lesson_id=lesson_id)
    db.add(db_materials)
    db.commit()
    db.refresh(db_materials)
    return db_materials

def get_lesson_materials(db: Session, lesson_id: uuid.UUID):
    """Get materials for a lesson."""
    return db.query(Materials).filter(Materials.lesson_id == lesson_id).first() 