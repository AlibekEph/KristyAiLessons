"""Main FastAPI application"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
import logging
from datetime import datetime

from .config import Settings
from .dependencies import (
    get_recording_service,
    get_transcription_service,
    get_ai_processor,
    get_storage_service
)
from .interfaces.recording import RecordingServiceInterface
from .interfaces.transcription import TranscriptionServiceInterface
from .interfaces.ai_processor import AIProcessorInterface, AIProcessingRequest
from .interfaces.storage import StorageServiceInterface, Lesson

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="KristyLessonRecords",
    description="""
## Автоматическая система записи и обработки онлайн-уроков

### Возможности:
- 🎥 Автоматическая запись уроков через Recall.ai
- 📝 Транскрипция через AssemblyAI
- 🤖 AI-обработка через YandexGPT
- 📚 Генерация учебных материалов

### Основные компоненты:
1. **Конспект урока** - структурированная информация о пройденном материале
2. **Домашнее задание** - упражнения и рекомендации
3. **Словарь** - ключевая лексика с переводом и примерами
    """,
    version="1.0.0",
    contact={
        "name": "KristyLessonRecords Support",
        "email": "support@kristylessons.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Settings
settings = Settings()


# Request/Response models
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
    id: str = Field(..., description="Уникальный ID урока", example="lesson_1234567890.123")
    status: str = Field(
        ..., 
        description="Статус обработки урока",
        example="recording",
        pattern="^(recording|transcribing|processing|completed|failed)$"
    )
    meeting_url: str = Field(..., description="URL встречи", example="https://zoom.us/j/1234567890")
    lesson_type: str = Field(..., description="Тип урока", example="chinese")
    created_at: datetime = Field(..., description="Время создания записи")
    transcript_available: bool = Field(False, description="Доступна ли транскрипция")
    materials_available: bool = Field(False, description="Доступны ли учебные материалы")


class WebhookRequest(BaseModel):
    """Webhook запрос"""
    event: str = Field(..., description="Тип события")
    data: Dict[str, Any] = Field(..., description="Данные события")


# API Endpoints
@app.get("/", tags=["Health"])
async def root():
    """
    Проверка состояния сервиса
    
    Возвращает статус работы сервиса.
    """
    return {"status": "ok", "service": "KristyLessonRecords"}


@app.post(
    "/lessons/record", 
    response_model=LessonResponse,
    tags=["Lessons"],
    summary="Начать запись урока",
    description="""
    Запускает процесс записи онлайн-урока.
    
    После вызова этого эндпоинта:
    1. Recall.ai бот присоединится к встрече
    2. Начнётся запись аудио/видео
    3. После окончания урока автоматически запустится транскрипция
    4. AI обработает транскрипцию и создаст учебные материалы
    """,
    responses={
        200: {
            "description": "Запись успешно начата",
            "content": {
                "application/json": {
                    "example": {
                        "id": "lesson_1234567890.123",
                        "status": "recording",
                        "meeting_url": "https://zoom.us/j/1234567890",
                        "lesson_type": "chinese",
                        "created_at": "2024-01-20T10:30:00",
                        "transcript_available": False,
                        "materials_available": False
                    }
                }
            }
        },
        500: {"description": "Ошибка при запуске записи"}
    }
)
async def start_recording(
    request: RecordLessonRequest,
    background_tasks: BackgroundTasks,
    recording_service: RecordingServiceInterface = Depends(get_recording_service),
    storage_service: StorageServiceInterface = Depends(get_storage_service)
):
    """Start recording a lesson"""
    
    try:
        # Create lesson record
        lesson = Lesson(
            id=f"lesson_{datetime.now().timestamp()}",
            meeting_url=request.meeting_url,
            lesson_type=request.lesson_type,
            student_id=request.student_id,
            teacher_id=request.teacher_id,
            status="recording",
            metadata=request.metadata or {}
        )
        
        # Save lesson
        lesson = await storage_service.save_lesson(lesson)
        
        # Start recording
        webhook_url = f"{settings.APP_URL}/webhooks/recall"
        recording_session = await recording_service.start_recording(
            meeting_url=request.meeting_url,
            webhook_url=webhook_url,
            metadata={
                "lesson_id": lesson.id,
                "lesson_type": request.lesson_type,
                "student_level": request.student_level
            }
        )
        
        # Update lesson with recording session ID
        lesson.recording_session_id = recording_session.id
        await storage_service.save_lesson(lesson)
        
        logger.info(f"Started recording for lesson {lesson.id}")
        
        return LessonResponse(
            id=lesson.id,
            status=lesson.status,
            meeting_url=lesson.meeting_url,
            lesson_type=lesson.lesson_type,
            created_at=lesson.created_at
        )
        
    except Exception as e:
        logger.error(f"Failed to start recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/lessons/{lesson_id}", 
    response_model=LessonResponse,
    tags=["Lessons"],
    summary="Получить информацию об уроке",
    description="Возвращает текущий статус и информацию об уроке",
    responses={
        200: {"description": "Информация об уроке"},
        404: {"description": "Урок не найден"}
    }
)
async def get_lesson(
    lesson_id: str = Path(..., description="ID урока", example="lesson_1234567890.123"),
    storage_service: StorageServiceInterface = Depends(get_storage_service)
):
    """Получить информацию об уроке"""
    
    lesson = await storage_service.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    return LessonResponse(
        id=lesson.id,
        status=lesson.status,
        meeting_url=lesson.meeting_url,
        lesson_type=lesson.lesson_type,
        created_at=lesson.created_at,
        transcript_available=lesson.transcription_id is not None,
        materials_available=lesson.materials_id is not None
    )


@app.get(
    "/lessons/{lesson_id}/transcript",
    tags=["Lessons"],
    summary="Получить транскрипцию урока",
    description="""
    Возвращает полную транскрипцию урока с временными метками и распознанными спикерами.
    
    Транскрипция включает:
    - Полный текст урока
    - Сегменты с временными метками
    - Информацию о спикерах
    - Язык транскрипции
    """,
    responses={
        200: {
            "description": "Транскрипция урока",
            "content": {
                "application/json": {
                    "example": {
                        "id": "transcript_123",
                        "text": "Преподаватель: Привет! Сегодня мы изучаем числа. На китайском один будет 一 (yī)...",
                        "segments": [
                            {
                                "text": "Привет! Сегодня мы изучаем числа.",
                                "start": 0.0,
                                "end": 3.5,
                                "speaker": "Teacher"
                            }
                        ],
                        "language": "ru",
                        "duration": 1800.0
                    }
                }
            }
        },
        404: {"description": "Урок или транскрипция не найдены"}
    }
)
async def get_transcript(
    lesson_id: str = Path(..., description="ID урока"),
    storage_service: StorageServiceInterface = Depends(get_storage_service)
):
    """Получить транскрипцию урока"""
    
    lesson = await storage_service.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    if not lesson.transcription_id:
        raise HTTPException(status_code=404, detail="Transcript not available")
    
    # Get transcript from storage
    transcript_data = await storage_service.get_json(f"transcript_{lesson.transcription_id}")
    if not transcript_data:
        raise HTTPException(status_code=404, detail="Transcript data not found")
    
    return transcript_data


@app.get(
    "/lessons/{lesson_id}/materials",
    tags=["Lessons"],
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
    lesson_id: str = Path(..., description="ID урока"),
    storage_service: StorageServiceInterface = Depends(get_storage_service)
):
    """Получить учебные материалы"""
    
    lesson = await storage_service.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    if not lesson.materials_id:
        raise HTTPException(status_code=404, detail="Materials not available")
    
    # Get materials from storage
    materials_data = await storage_service.get_json(f"materials_{lesson.materials_id}")
    if not materials_data:
        raise HTTPException(status_code=404, detail="Materials data not found")
    
    return materials_data


@app.get(
    "/debug/api-logs",
    tags=["Debug"],
    summary="Просмотреть логи API запросов",
    description="""
    Возвращает логи всех API запросов к внешним сервисам с возможностью воспроизведения через curl.
    
    Полезно для отладки проблем с интеграциями:
    - Recall.ai
    - AssemblyAI
    - YandexGPT
    
    Каждый лог содержит готовую curl команду для воспроизведения запроса.
    """,
    responses={
        200: {
            "description": "Логи API запросов",
            "content": {
                "application/json": {
                    "example": {
                        "logs": [
                            {
                                "request_id": "recall_20240120_143022_123456",
                                "timestamp": "2024-01-20T14:30:22.123456",
                                "service": "recall",
                                "method": "POST",
                                "url": "https://api.recall.ai/api/v1/bot",
                                "status_code": 200,
                                "curl_command": "curl -X POST \\\n  -H \"Authorization: ***HIDDEN***\" \\\n  -d '{\"meeting_url\":\"https://zoom.us/j/123\"}' \\\n  \"https://api.recall.ai/api/v1/bot\""
                            }
                        ],
                        "total": 1,
                        "service_filter": None,
                        "log_directory": "/app/logs/api_requests"
                    }
                }
            }
        }
    }
)
async def get_api_logs(
    service: Optional[str] = Query(None, description="Фильтр по сервису (recall, assemblyai, yandexgpt)"),
    date: Optional[str] = Query(None, description="Дата в формате YYYYMMDD"),
    limit: int = Query(50, description="Максимальное количество записей", ge=1, le=1000)
):
    """Получить логи API запросов для отладки"""
    
    try:
        from .utils.api_logger import get_api_logs as get_logs
        
        logs_data = await get_logs(
            service_name=service,
            date=date,
            limit=limit
        )
        
        return logs_data
        
    except Exception as e:
        logger.error(f"Failed to get API logs: {e}")
        return {
            "logs": [],
            "total": 0,
            "error": str(e),
            "service_filter": service,
            "log_directory": "/app/logs/api_requests"
        }


@app.post(
    "/webhooks/recall",
    tags=["Webhooks"],
    summary="Webhook для Recall.ai",
    description="Обрабатывает уведомления от Recall.ai о статусе записи",
    include_in_schema=False  # Скрываем из публичной документации
)
async def handle_recall_webhook(
    webhook_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    recording_service: RecordingServiceInterface = Depends(get_recording_service),
    transcription_service: TranscriptionServiceInterface = Depends(get_transcription_service),
    storage_service: StorageServiceInterface = Depends(get_storage_service)
):
    """Обработка webhooks от Recall.ai"""
    
    try:
        event_type = webhook_data.get("event")
        bot_id = webhook_data.get("data", {}).get("bot_id")
        
        logger.info(f"Received Recall webhook: {event_type} for bot {bot_id}")
        
        # Handle recording completed event
        if event_type == "bot.call_ended":
            # Get recording session
            recording_session = await recording_service.get_recording_status(bot_id)
            
            # Find lesson by recording session ID
            lessons = await storage_service.list_lessons()
            lesson = next((l for l in lessons if l.recording_session_id == bot_id), None)
            
            if lesson:
                # Update lesson status
                lesson.status = "transcribing"
                lesson.ended_at = datetime.now()
                await storage_service.save_lesson(lesson)
                
                # Start transcription in background
                background_tasks.add_task(
                    process_recording,
                    lesson.id,
                    recording_session.recording_url,
                    transcription_service,
                    storage_service
                )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Failed to handle Recall webhook: {e}")
        return {"status": "error", "message": str(e)}


@app.post(
    "/webhooks/assemblyai",
    tags=["Webhooks"],
    summary="Webhook для AssemblyAI",
    description="Обрабатывает уведомления от AssemblyAI о готовности транскрипции",
    include_in_schema=False  # Скрываем из публичной документации
)
async def handle_assemblyai_webhook(
    webhook_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    transcription_service: TranscriptionServiceInterface = Depends(get_transcription_service),
    ai_processor: AIProcessorInterface = Depends(get_ai_processor),
    storage_service: StorageServiceInterface = Depends(get_storage_service)
):
    """Обработка webhooks от AssemblyAI"""
    
    try:
        transcript_id = webhook_data.get("transcript_id")
        status = webhook_data.get("status")
        
        logger.info(f"Received AssemblyAI webhook: {status} for transcript {transcript_id}")
        
        # Handle transcription completed
        if status == "completed" and transcript_id:
            # Get transcription result
            transcription_result = await transcription_service.get_transcription_result(transcript_id)
            
            # Find lesson by transcription ID
            lessons = await storage_service.list_lessons()
            lesson = next((l for l in lessons if l.transcription_id == transcript_id), None)
            
            if lesson:
                # Save transcript
                await storage_service.save_json(
                    f"transcript_{transcript_id}",
                    {
                        "id": transcription_result.id,
                        "text": transcription_result.text,
                        "segments": [
                            {
                                "text": seg.text,
                                "start": seg.start,
                                "end": seg.end,
                                "speaker": seg.speaker
                            }
                            for seg in transcription_result.segments
                        ],
                        "language": transcription_result.language_code,
                        "duration": transcription_result.duration
                    }
                )
                
                # Update lesson status
                lesson.status = "processing"
                await storage_service.save_lesson(lesson)
                
                # Process with AI in background
                background_tasks.add_task(
                    process_transcript,
                    lesson.id,
                    transcription_result.text,
                    lesson.lesson_type,
                    lesson.metadata.get("student_level"),
                    ai_processor,
                    storage_service
                )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Failed to handle AssemblyAI webhook: {e}")
        return {"status": "error", "message": str(e)}


# Background tasks
async def process_recording(
    lesson_id: str,
    recording_url: str,
    transcription_service: TranscriptionServiceInterface,
    storage_service: StorageServiceInterface
):
    """Process recording and start transcription"""
    
    try:
        logger.info(f"Processing recording for lesson {lesson_id}")
        
        # Get lesson
        lesson = await storage_service.get_lesson(lesson_id)
        if not lesson:
            logger.error(f"Lesson {lesson_id} not found")
            return
        
        # Start transcription
        webhook_url = f"{settings.APP_URL}/webhooks/assemblyai"
        
        if lesson.lesson_type == "chinese":
            # Use multilingual transcription
            transcription_result = await transcription_service.transcribe_multilingual(
                audio_url=recording_url,
                primary_language="ru",
                secondary_languages=["zh"],
                webhook_url=webhook_url,
                metadata={"lesson_id": lesson_id}
            )
        else:
            # Regular transcription
            transcription_result = await transcription_service.transcribe_audio(
                audio_url=recording_url,
                language_code="ru",
                webhook_url=webhook_url,
                metadata={"lesson_id": lesson_id}
            )
        
        # Update lesson with transcription ID
        lesson.transcription_id = transcription_result.id
        await storage_service.save_lesson(lesson)
        
        logger.info(f"Started transcription {transcription_result.id} for lesson {lesson_id}")
        
    except Exception as e:
        logger.error(f"Failed to process recording: {e}")
        # Update lesson status to failed
        lesson = await storage_service.get_lesson(lesson_id)
        if lesson:
            lesson.status = "failed"
            await storage_service.save_lesson(lesson)


async def process_transcript(
    lesson_id: str,
    transcript: str,
    lesson_type: str,
    student_level: Optional[str],
    ai_processor: AIProcessorInterface,
    storage_service: StorageServiceInterface
):
    """Process transcript with AI"""
    
    try:
        logger.info(f"Processing transcript for lesson {lesson_id}")
        
        # Get lesson
        lesson = await storage_service.get_lesson(lesson_id)
        if not lesson:
            logger.error(f"Lesson {lesson_id} not found")
            return
        
        # Process with AI
        request = AIProcessingRequest(
            transcript=transcript,
            lesson_type=lesson_type,
            student_level=student_level,
            lesson_duration=lesson.ended_at.timestamp() - lesson.started_at.timestamp() if lesson.started_at and lesson.ended_at else None,
            metadata={"lesson_id": lesson_id}
        )
        
        materials = await ai_processor.process_lesson(request)
        
        # Save materials
        materials_id = f"mat_{datetime.now().timestamp()}"
        await storage_service.save_json(
            f"materials_{materials_id}",
            {
                "lesson_id": lesson_id,
                "original_transcript": materials.original_transcript,
                "corrected_transcript": materials.corrected_transcript,
                "summary": materials.summary,
                "homework": materials.homework,
                "notes": materials.notes,
                "vocabulary": materials.key_vocabulary,
                "created_at": materials.created_at.isoformat()
            }
        )
        
        # Update lesson
        lesson.materials_id = materials_id
        lesson.status = "completed"
        await storage_service.save_lesson(lesson)
        
        logger.info(f"Completed processing for lesson {lesson_id}")
        
    except Exception as e:
        logger.error(f"Failed to process transcript: {e}")
        # Update lesson status to failed
        lesson = await storage_service.get_lesson(lesson_id)
        if lesson:
            lesson.status = "failed"
            await storage_service.save_lesson(lesson) 