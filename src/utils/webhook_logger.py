"""Утилита для логирования webhook событий"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class WebhookLogger:
    """Класс для логирования webhook событий"""
    
    def __init__(self, log_dir: str = "logs/webhooks"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Настройка отдельного logger'а для webhook'ов
        self.logger = logging.getLogger("webhook_events")
        self.logger.setLevel(logging.INFO)
        
        # Если handler'ы еще не добавлены
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
            # File handler
            log_file = self.log_dir / "webhook_events.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    async def log_webhook_event(
        self,
        service: str,
        event_type: str,
        webhook_data: Dict[str, Any],
        processing_result: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Логирует webhook событие в файлы и консоль
        
        Args:
            service: Название сервиса (recall, assemblyai, etc.)
            event_type: Тип события
            webhook_data: Полные данные webhook'а
            processing_result: Результат обработки события
            
        Returns:
            ID события для ссылки
        """
        timestamp = datetime.utcnow()
        event_id = f"{service}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Структурированные данные события
        event_log = {
            "event_id": event_id,
            "timestamp": timestamp.isoformat(),
            "service": service,
            "event_type": event_type,
            "webhook_data": webhook_data,
            "processing_result": processing_result
        }
        
        # Логирование в консоль
        bot_id = self._extract_bot_id(webhook_data)
        lesson_id = processing_result.get("lesson_id") if processing_result else None
        
        log_message = f"[{service.upper()}] {event_type}"
        if bot_id:
            log_message += f" | Bot: {bot_id}"
        if lesson_id:
            log_message += f" | Lesson: {lesson_id}"
        
        self.logger.info(log_message)
        
        # Детализация в консоль
        if processing_result:
            if processing_result.get("status_changed"):
                old_status = processing_result.get("old_status")
                new_status = processing_result.get("new_status")
                self.logger.info(f"Status updated: {old_status} → {new_status}")
            
            if processing_result.get("timestamps_updated"):
                for update in processing_result.get("timestamps_updated", []):
                    self.logger.info(f"Timestamp updated: {update}")
        
        # Сохранение в JSON файл
        await self._save_to_file(event_id, event_log)
        
        return event_id
    
    def _extract_bot_id(self, webhook_data: Dict[str, Any]) -> Optional[str]:
        """Извлекает bot_id из webhook данных"""
        try:
            return webhook_data.get("data", {}).get("bot", {}).get("id")
        except:
            return None
    
    async def _save_to_file(self, event_id: str, event_log: Dict[str, Any]) -> None:
        """Сохраняет событие в JSON файл"""
        try:
            # Создаем директорию по дате
            date_str = datetime.utcnow().strftime('%Y%m%d')
            date_dir = self.log_dir / date_str
            date_dir.mkdir(exist_ok=True)
            
            # Имя файла
            filename = f"{event_id}.json"
            filepath = date_dir / filename
            
            # Сохраняем JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(event_log, f, indent=2, ensure_ascii=False, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save webhook event to file: {e}")
    
    def log_error(self, service: str, event_type: str, error: Exception, webhook_data: Dict[str, Any] = None):
        """Логирует ошибку обработки webhook'а"""
        error_message = f"[{service.upper()}] ERROR processing {event_type}: {str(error)}"
        self.logger.error(error_message)
        
        if webhook_data:
            bot_id = self._extract_bot_id(webhook_data)
            if bot_id:
                self.logger.error(f"Bot ID: {bot_id}")


# Глобальный экземпляр logger'а
webhook_logger = WebhookLogger()


async def log_webhook_event(
    service: str,
    event_type: str,
    webhook_data: Dict[str, Any],
    processing_result: Optional[Dict[str, Any]] = None
) -> str:
    """Удобная функция для логирования webhook событий"""
    return await webhook_logger.log_webhook_event(service, event_type, webhook_data, processing_result)


def log_webhook_error(service: str, event_type: str, error: Exception, webhook_data: Dict[str, Any] = None):
    """Удобная функция для логирования ошибок webhook'ов"""
    webhook_logger.log_error(service, event_type, error, webhook_data) 