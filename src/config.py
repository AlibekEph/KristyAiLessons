"""Application configuration"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "KristyLessonRecords"
    APP_PORT: int = 8000
    APP_ENV: str = "development"
    APP_URL: str = "https://ai.dr-study.ru"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/db"
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Recall.ai
    RECALL_API_KEY: str
    RECALL_WEBHOOK_URL: str = "https://ai.dr-study.ru/webhooks/recall"
    RECALL_REGION: str = "us-west-2"
    
    # AssemblyAI
    ASSEMBLYAI_API_KEY: str
    
    # YandexGPT
    YANDEX_FOLDER_ID: str
    YANDEX_API_KEY: str
    YANDEX_MODEL_URI: Optional[str] = None
    
    # Storage
    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = "/app/storage"
    
    # Languages
    SUPPORTED_LANGUAGES: str = "zh,en,ru"
    DEFAULT_LANGUAGE: str = "ru"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    class Config:
        # Проверяем сначала .env в контейнере, затем в корне проекта
        env_file = "/app/.env" if os.path.exists("/app/.env") else ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings 