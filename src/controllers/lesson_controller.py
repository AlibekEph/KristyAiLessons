"""Lesson controller with business logic."""

import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc

from ..models import Lesson, Transcript, Materials
from ..filters import LessonFilter, LessonFilterParams
from .. import schemas


class LessonController:
    """Controller for lesson-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_lesson_by_id(self, lesson_id: uuid.UUID) -> Optional[Lesson]:
        """Get a lesson by ID with related data."""
        return (
            self.db.query(Lesson)
            .options(
                joinedload(Lesson.transcript),
                joinedload(Lesson.materials)
            )
            .filter(Lesson.id == lesson_id)
            .first()
        )
    
    def get_lessons_with_pagination(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[LessonFilterParams] = None,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ) -> Tuple[List[Lesson], int]:
        """
        Get lessons with pagination and filtering.
        
        Returns:
            Tuple of (lessons_list, total_count)
        """
        # Base query with eager loading
        query = (
            self.db.query(Lesson)
            .options(
                joinedload(Lesson.transcript),
                joinedload(Lesson.materials)
            )
        )
        
        # Apply filters
        if filters:
            query = LessonFilter.apply_filters(query, filters)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply ordering
        order_column = LessonFilter.get_order_by_column(order_by)
        if order_direction.lower() == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        # Apply pagination
        offset = (page - 1) * page_size
        lessons = query.offset(offset).limit(page_size).all()
        
        return lessons, total_count
    
    def create_lesson(self, lesson_data: schemas.LessonCreate) -> Lesson:
        """Create a new lesson."""
        db_lesson = Lesson(**lesson_data.dict())
        self.db.add(db_lesson)
        self.db.commit()
        self.db.refresh(db_lesson)
        return db_lesson
    
    def update_lesson_status(self, lesson_id: uuid.UUID, status: str) -> Optional[Lesson]:
        """Update lesson status."""
        lesson = self.get_lesson_by_id(lesson_id)
        if lesson:
            lesson.status = status
            self.db.commit()
            self.db.refresh(lesson)
        return lesson
    
    def update_lesson(self, lesson_id: uuid.UUID, lesson_data: dict) -> Optional[Lesson]:
        """Update lesson with new data."""
        lesson = self.get_lesson_by_id(lesson_id)
        if lesson:
            for key, value in lesson_data.items():
                if hasattr(lesson, key) and value is not None:
                    setattr(lesson, key, value)
            self.db.commit()
            self.db.refresh(lesson)
        return lesson
    
    def get_lessons_statistics(self, filters: Optional[LessonFilterParams] = None) -> dict:
        """Get lessons statistics."""
        query = self.db.query(Lesson)
        
        if filters:
            query = LessonFilter.apply_filters(query, filters)
        
        total_lessons = query.count()
        
        # Count by status
        status_counts = {}
        for status in ["pending", "recording", "transcribing", "processing", "completed", "failed"]:
            count = query.filter(Lesson.status == status).count()
            if count > 0:
                status_counts[status] = count
        
        # Count by lesson type
        type_counts = {}
        for lesson_type in ["chinese", "english"]:
            count = query.filter(Lesson.lesson_type == lesson_type).count()
            if count > 0:
                type_counts[lesson_type] = count
        
        # Count lessons with materials/transcripts
        with_transcript = query.filter(Lesson.transcript.has()).count()
        with_materials = query.filter(Lesson.materials.has()).count()
        
        return {
            "total_lessons": total_lessons,
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "with_transcript": with_transcript,
            "with_materials": with_materials
        }
    
    def delete_lesson(self, lesson_id: uuid.UUID) -> bool:
        """Delete a lesson and related data."""
        lesson = self.get_lesson_by_id(lesson_id)
        if lesson:
            self.db.delete(lesson)
            self.db.commit()
            return True
        return False 