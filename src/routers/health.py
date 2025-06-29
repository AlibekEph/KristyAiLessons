"""Health check API routes"""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/")
async def root():
    """
    Проверка состояния сервиса
    
    Возвращает статус работы сервиса.
    """
    return {"status": "ok", "service": "KristyLessonRecords"} 