"""Main FastAPI application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .config import Settings
from .routers import health, lessons_api, webhooks_api, debug
from .api.endpoints import test_language_detection

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
- 📝 Транскрипция через AssemblyAI с автоматическим определением языка
- 🤖 AI-обработка через YandexGPT
- 📚 Генерация учебных материалов
- 🌐 Поддержка многоязычных уроков (русский + китайский, русский + английский)

### Основные компоненты:
1. **Конспект урока** - структурированная информация о пройденном материале
2. **Домашнее задание** - упражнения и рекомендации
3. **Словарь** - ключевая лексика с переводом и примерами

### Новые возможности:
- 🔍 Автоматическое определение языка без hardcoded слов
- 📊 Интеллектуальная оценка качества транскрипции
- 🎯 Адаптация под тип урока (китайский/английский)
    """,
    version="1.0.1",
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

# Include routers
app.include_router(health.router)
app.include_router(lessons_api.router)
app.include_router(webhooks_api.router)
app.include_router(debug.router)
app.include_router(test_language_detection.router) 