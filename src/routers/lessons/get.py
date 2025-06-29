"""API endpoint to get lesson details."""

import uuid
from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy import text

from ...dependencies import get_storage_service
from ...interfaces.storage import StorageServiceInterface
from .models import LessonResponse

router = APIRouter()

@router.get(
    "/{lesson_id}",
    response_model=LessonResponse,
    summary="Получить информацию об уроке",
    description="""
    Возвращает детальную информацию об уроке, включая:
    - Статус урока
    - Доступность транскрипции
    - Доступность материалов
    - Метаданные урока
    """,
    responses={
        404: {"description": "Урок не найден"}
    }
)
async def get_lesson(
    lesson_id: uuid.UUID = Path(..., description="ID урока"),
    storage_service: StorageServiceInterface = Depends(get_storage_service)
):
    """Получить информацию об уроке"""
    
    lesson = await storage_service.get_lesson(str(lesson_id))
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Check transcript availability via direct database query
    transcript_available = False
    materials_available = False
    
    try:
        # Get database session
        db = storage_service.db
        result = db.execute(
            text("SELECT transcript_id FROM lessons WHERE id = :lesson_id"),
            {"lesson_id": str(lesson_id)}
        )
        row = result.fetchone()
        if row and row[0]:
            transcript_available = True
    except Exception as e:
        print(f"Error checking transcript availability: {e}")
    
    return LessonResponse(
        id=lesson.id,
        status=lesson.status,
        meeting_url=lesson.meeting_url,
        lesson_type=lesson.lesson_type,
        created_at=lesson.created_at,
        transcript_available=transcript_available,
        materials_available=materials_available
    ) 