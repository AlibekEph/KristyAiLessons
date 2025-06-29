"""Debug API routes"""

from fastapi import APIRouter, Query
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get(
    "/api-logs",
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
        from ..utils.api_logger import get_api_logs as get_logs
        
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