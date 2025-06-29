"""API endpoint to get lessons list with pagination and filtering."""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query

from ...database import get_db
from ...controllers import LessonController
from ...filters import LessonFilterParams
from ...schemas import (
    LessonListResponse, 
    LessonListItem, 
    PaginationParams, 
    OrderDirection,
    LessonStatistics
)
from sqlalchemy.orm import Session

router = APIRouter()


@router.get(
    "/",
    response_model=LessonListResponse,
    summary="Получить список уроков",
    description="""
    Получить список уроков с пагинацией и фильтрацией.
    
    ### Фильтры:
    - **status** - статус урока (pending, recording, transcribing, processing, completed, failed)  
    - **lesson_type** - тип урока (chinese, english)
    - **student_id** - ID студента
    - **teacher_id** - ID преподавателя
    - **created_after** - уроки созданные после указанной даты
    - **created_before** - уроки созданные до указанной даты
    - **search** - поиск по URL встречи и метаданным
    - **has_transcript** - есть ли транскрипция
    - **has_materials** - есть ли учебные материалы
    
    ### Пагинация:
    - **page** - номер страницы (начиная с 1)
    - **page_size** - количество элементов на странице (max 100)
    - **order_by** - поле для сортировки
    - **order_direction** - направление сортировки (asc/desc)
    """,
    responses={
        200: {"description": "Список уроков с пагинацией"}
    }
)
async def get_lessons_list(
    # Pagination parameters
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    order_by: str = Query("created_at", description="Поле для сортировки"),
    order_direction: OrderDirection = Query(OrderDirection.DESC, description="Направление сортировки"),
    
    # Filter parameters
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    statuses: Optional[List[str]] = Query(None, description="Фильтр по нескольким статусам"),
    lesson_type: Optional[str] = Query(None, description="Фильтр по типу урока"),
    lesson_types: Optional[List[str]] = Query(None, description="Фильтр по нескольким типам"),
    student_id: Optional[str] = Query(None, description="Фильтр по ID студента"),
    teacher_id: Optional[str] = Query(None, description="Фильтр по ID преподавателя"),
    created_after: Optional[datetime] = Query(None, description="Уроки созданные после"),
    created_before: Optional[datetime] = Query(None, description="Уроки созданные до"),
    started_after: Optional[datetime] = Query(None, description="Уроки начатые после"),
    started_before: Optional[datetime] = Query(None, description="Уроки начатые до"),
    search: Optional[str] = Query(None, description="Поиск по URL и метаданным"),
    has_transcript: Optional[bool] = Query(None, description="Есть ли транскрипция"),
    has_materials: Optional[bool] = Query(None, description="Есть ли учебные материалы"),
    
    db: Session = Depends(get_db)
):
    """Получить список уроков с пагинацией и фильтрацией."""
    
    # Create filter parameters
    filters = LessonFilterParams(
        status=status,
        statuses=statuses,
        lesson_type=lesson_type,
        lesson_types=lesson_types,
        student_id=student_id,
        teacher_id=teacher_id,
        created_after=created_after,
        created_before=created_before,
        started_after=started_after,
        started_before=started_before,
        search=search,
        has_transcript=has_transcript,
        has_materials=has_materials
    )
    
    # Initialize controller
    controller = LessonController(db)
    
    # Get lessons with pagination
    lessons, total_count = controller.get_lessons_with_pagination(
        page=page,
        page_size=page_size,
        filters=filters,
        order_by=order_by,
        order_direction=order_direction.value
    )
    
    # Convert to list items
    lesson_items = []
    for lesson in lessons:
        lesson_item = LessonListItem(
            id=lesson.id,
            meeting_url=lesson.meeting_url,
            lesson_type=lesson.lesson_type,
            student_id=lesson.student_id,
            teacher_id=lesson.teacher_id,
            status=lesson.status,
            created_at=lesson.created_at,
            started_at=lesson.started_at,
            ended_at=lesson.ended_at,
            has_transcript=lesson.transcript is not None,
            has_materials=lesson.materials is not None
        )
        lesson_items.append(lesson_item)
    
    # Create paginated response
    return LessonListResponse.create(
        items=lesson_items,
        page=page,
        page_size=page_size,
        total_items=total_count
    )


@router.get(
    "/statistics",
    response_model=LessonStatistics,
    summary="Получить статистику по урокам",
    description="Получить статистику по урокам с возможностью фильтрации",
    responses={
        200: {"description": "Статистика по урокам"}
    }
)
async def get_lessons_statistics(
    # Filter parameters (same as in list endpoint)
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    lesson_type: Optional[str] = Query(None, description="Фильтр по типу урока"),
    student_id: Optional[str] = Query(None, description="Фильтр по ID студента"),
    teacher_id: Optional[str] = Query(None, description="Фильтр по ID преподавателя"),
    created_after: Optional[datetime] = Query(None, description="Уроки созданные после"),
    created_before: Optional[datetime] = Query(None, description="Уроки созданные до"),
    
    db: Session = Depends(get_db)
):
    """Получить статистику по урокам."""
    
    # Create filter parameters
    filters = LessonFilterParams(
        status=status,
        lesson_type=lesson_type,
        student_id=student_id,
        teacher_id=teacher_id,
        created_after=created_after,
        created_before=created_before
    )
    
    # Initialize controller
    controller = LessonController(db)
    
    # Get statistics
    stats = controller.get_lessons_statistics(filters)
    
    return LessonStatistics(**stats) 