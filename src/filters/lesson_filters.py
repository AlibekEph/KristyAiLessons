"""Lesson filtering utilities."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy.orm import Query
from sqlalchemy import and_, or_

from ..models import Lesson


class LessonFilterParams(BaseModel):
    """Parameters for filtering lessons."""
    
    # Status filters
    status: Optional[str] = Field(None, description="Filter by lesson status")
    statuses: Optional[List[str]] = Field(None, description="Filter by multiple statuses")
    
    # Type filters
    lesson_type: Optional[str] = Field(None, description="Filter by lesson type")
    lesson_types: Optional[List[str]] = Field(None, description="Filter by multiple lesson types")
    
    # User filters
    student_id: Optional[str] = Field(None, description="Filter by student ID")
    teacher_id: Optional[str] = Field(None, description="Filter by teacher ID")
    
    # Date filters
    created_after: Optional[datetime] = Field(None, description="Filter lessons created after this date")
    created_before: Optional[datetime] = Field(None, description="Filter lessons created before this date")
    started_after: Optional[datetime] = Field(None, description="Filter lessons started after this date")
    started_before: Optional[datetime] = Field(None, description="Filter lessons started before this date")
    
    # Search
    search: Optional[str] = Field(None, description="Search in meeting URL and metadata")
    
    # Boolean filters
    has_transcript: Optional[bool] = Field(None, description="Filter by transcript availability")
    has_materials: Optional[bool] = Field(None, description="Filter by materials availability")


class LessonFilter:
    """Utility class for applying filters to lesson queries."""
    
    @staticmethod
    def apply_filters(query: Query, filters: LessonFilterParams) -> Query:
        """Apply filters to the lesson query."""
        
        # Status filters
        if filters.status:
            query = query.filter(Lesson.status == filters.status)
        elif filters.statuses:
            query = query.filter(Lesson.status.in_(filters.statuses))
        
        # Type filters
        if filters.lesson_type:
            query = query.filter(Lesson.lesson_type == filters.lesson_type)
        elif filters.lesson_types:
            query = query.filter(Lesson.lesson_type.in_(filters.lesson_types))
        
        # User filters
        if filters.student_id:
            query = query.filter(Lesson.student_id == filters.student_id)
        if filters.teacher_id:
            query = query.filter(Lesson.teacher_id == filters.teacher_id)
        
        # Date filters
        if filters.created_after:
            query = query.filter(Lesson.created_at >= filters.created_after)
        if filters.created_before:
            query = query.filter(Lesson.created_at <= filters.created_before)
        if filters.started_after:
            query = query.filter(Lesson.started_at >= filters.started_after)
        if filters.started_before:
            query = query.filter(Lesson.started_at <= filters.started_before)
        
        # Search filter
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Lesson.meeting_url.ilike(search_term),
                    Lesson.lesson_metadata.astext.ilike(search_term)
                )
            )
        
        # Boolean filters for related data
        if filters.has_transcript is not None:
            if filters.has_transcript:
                query = query.filter(Lesson.transcript.has())
            else:
                query = query.filter(~Lesson.transcript.has())
        
        if filters.has_materials is not None:
            if filters.has_materials:
                query = query.filter(Lesson.materials.has())
            else:
                query = query.filter(~Lesson.materials.has())
        
        return query
    
    @staticmethod
    def get_order_by_column(order_by: str):
        """Get the column to order by."""
        order_mapping = {
            "created_at": Lesson.created_at,
            "started_at": Lesson.started_at, 
            "ended_at": Lesson.ended_at,
            "status": Lesson.status,
            "lesson_type": Lesson.lesson_type,
        }
        return order_mapping.get(order_by, Lesson.created_at) 