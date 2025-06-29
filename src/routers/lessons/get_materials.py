"""API endpoint to get the educational materials for a lesson."""

import uuid
from fastapi import APIRouter, HTTPException, Depends, Path

from ...dependencies import get_storage_service
from ...interfaces.storage import StorageServiceInterface

router = APIRouter()

@router.get(
    "/{lesson_id}/materials",
    summary="Получить учебные материалы",
    description="""
    Возвращает сгенерированные AI учебные материалы на основе транскрипции урока.

    Материалы включают:
    - **Исправленная транскрипция** - с добавленными иероглифами и пиньинь
    - **Конспект урока** - структурированная информация о пройденном материале
    - **Домашнее задание** - упражнения и задания для закрепления
    - **Краткое описание** - что изучали на уроке
    - **Словарь** - ключевая лексика с переводом
    """,
    responses={
        200: {
            "description": "Учебные материалы",
            "content": {
                "application/json": {
                    "example": {
                        "lesson_id": "lesson_1234567890.123",
                        "corrected_transcript": "Привет! Сегодня мы изучаем числа. На китайском один будет 一 (yī), два - 二 (èr)...",
                        "summary": "## Основная тема урока\nЧисла от 1 до 10 на китайском языке\n\n## Изученная лексика\n- 一 (yī) - один\n- 二 (èr) - два...",
                        "homework": "## Упражнения на новую лексику\n1. Напишите числа от 1 до 10 иероглифами\n2. Запишите аудио с произношением...",
                        "notes": "На уроке изучили базовые числа от 1 до 10. Особое внимание уделили правильному произношению тонов.",
                        "vocabulary": [
                            {
                                "word": "一",
                                "pinyin": "yī",
                                "translation": "один",
                                "example": "一个人 (yī ge rén) - один человек"
                            },
                            {
                                "word": "二",
                                "pinyin": "èr",
                                "translation": "два",
                                "example": "二十 (èr shí) - двадцать"
                            }
                        ]
                    }
                }
            }
        },
        404: {"description": "Урок или материалы не найдены"}
    }
)
async def get_materials(
    lesson_id: uuid.UUID = Path(..., description="ID урока"),
    storage_service: StorageServiceInterface = Depends(get_storage_service)
):
    """Получить учебные материалы"""

    lesson = await storage_service.get_lesson(str(lesson_id))
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    if not lesson.materials_id:
        raise HTTPException(status_code=404, detail="Materials not found")

    # Get materials data from storage
    materials_data = await storage_service.get_json(f"materials_{lesson_id}")
    if not materials_data:
        raise HTTPException(status_code=404, detail="Materials not found")

    return materials_data 