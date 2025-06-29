"""Pydantic schemas for data validation."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime
from enum import Enum
import uuid

# Generic type for pagination
T = TypeVar('T')


class OrderDirection(str, Enum):
    """Order direction enum."""
    ASC = "asc"
    DESC = "desc"


class LessonStatus(str, Enum):
    """Lesson status enum."""
    PENDING = "pending"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class LessonType(str, Enum):
    """Lesson type enum."""
    CHINESE = "chinese"
    ENGLISH = "english"


# Base schemas
class TranscriptBase(BaseModel):
    text: str
    segments: Optional[List[Dict[str, Any]]] = None
    language_code: Optional[str] = None
    duration: Optional[str] = None

class MaterialsBase(BaseModel):
    original_transcript: Optional[str] = None
    corrected_transcript: Optional[str] = None
    summary: Optional[str] = None
    homework: Optional[str] = None
    notes: Optional[str] = None
    key_vocabulary: Optional[List[Dict[str, Any]]] = None

class LessonBase(BaseModel):
    meeting_url: str
    lesson_type: str
    student_id: Optional[str] = None
    teacher_id: Optional[str] = None
    status: Optional[str] = "pending"
    recording_session_id: Optional[str] = None  # Deprecated, use recall_bot_id
    recall_bot_id: Optional[str] = None  # Bot ID from Recall.ai API
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    lesson_metadata: Optional[Dict[str, Any]] = None

# Schemas for creation
class TranscriptCreate(TranscriptBase):
    id: Optional[uuid.UUID] = None  # Allow setting custom ID
    transcript_metadata: Optional[Dict[str, Any]] = None  # Renamed from metadata

class MaterialsCreate(MaterialsBase):
    pass

class LessonCreate(LessonBase):
    pass

# Schemas for reading
class Transcript(TranscriptBase):
    id: uuid.UUID
    lesson_id: uuid.UUID
    transcript_metadata: Optional[Dict[str, Any]] = None  # Renamed from metadata
    created_at: datetime

    class Config:
        from_attributes = True

class Materials(MaterialsBase):
    id: uuid.UUID
    lesson_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class Lesson(LessonBase):
    id: uuid.UUID
    created_at: datetime
    transcript: Optional[Transcript] = None
    materials: Optional[Materials] = None

    class Config:
        from_attributes = True


# Pagination schemas
class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1, description="Page number (starting from 1)")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page")
    order_by: str = Field("created_at", description="Field to order by")
    order_direction: OrderDirection = Field(OrderDirection.DESC, description="Order direction")


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    meta: PaginationMeta
    
    @classmethod
    def create(
        cls,
        items: List[T],
        page: int,
        page_size: int,
        total_items: int
    ):
        """Create a paginated response."""
        total_pages = (total_items + page_size - 1) // page_size
        
        return cls(
            items=items,
            meta=PaginationMeta(
                page=page,
                page_size=page_size,
                total_items=total_items,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1
            )
        )


# Lesson list schemas
class LessonListItem(BaseModel):
    """Lesson item for list view."""
    id: uuid.UUID
    meeting_url: str
    lesson_type: str
    student_id: Optional[str] = None
    teacher_id: Optional[str] = None
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    has_transcript: bool = False
    has_materials: bool = False

    class Config:
        from_attributes = True


class LessonListResponse(PaginatedResponse[LessonListItem]):
    """Paginated response for lesson list."""
    pass


# Statistics schema
class LessonStatistics(BaseModel):
    """Lesson statistics."""
    total_lessons: int
    status_distribution: Dict[str, int]
    type_distribution: Dict[str, int]
    with_transcript: int
    with_materials: int 