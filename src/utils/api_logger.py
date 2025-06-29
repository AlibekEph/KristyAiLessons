"""API request logger that formats requests as curl commands"""

import json
import logging
import os
from typing import Dict, Any, Optional, Union
from datetime import datetime
import aiofiles
from pathlib import Path

# Создаем отдельный логгер для API запросов
api_logger = logging.getLogger("api_requests")
api_logger.setLevel(logging.DEBUG)

# Директория для логов
LOG_DIR = Path("/app/logs/api_requests")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Файл для curl команд
CURL_LOG_FILE = LOG_DIR / f"curl_commands_{datetime.now().strftime('%Y%m%d')}.log"

# Настройка файлового хендлера
file_handler = logging.FileHandler(CURL_LOG_FILE)
file_handler.setLevel(logging.DEBUG)
api_logger.addHandler(file_handler)

# Также выводим в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
api_logger.addHandler(console_handler)


async def log_api_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    data: Optional[Union[str, bytes]] = None,
    service_name: str = "unknown",
    request_id: Optional[str] = None
) -> str:
    """
    Логирует API запрос в формате curl команды
    
    Args:
        method: HTTP метод (GET, POST, etc.)
        url: URL запроса
        headers: Заголовки запроса
        json_data: JSON данные для отправки
        data: Raw данные для отправки
        service_name: Имя сервиса (recall, assemblyai, yandex)
        request_id: ID запроса для отслеживания
        
    Returns:
        Сформированная curl команда
    """
    
    # Генерируем ID запроса если не передан
    if not request_id:
        request_id = f"{service_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    # Формируем curl команду
    curl_parts = ["curl", "-X", method]
    
    # Добавляем заголовки
    if headers:
        for key, value in headers.items():
            # Скрываем чувствительные данные
            if key.lower() in ["authorization", "api-key", "x-api-key"]:
                # Показываем только первые 10 символов токена
                if len(value) > 20:
                    masked_value = f"{value[:15]}...{value[-5:]}"
                else:
                    masked_value = "***HIDDEN***"
                curl_parts.extend(["-H", f'"{key}: {masked_value}"'])
            else:
                curl_parts.extend(["-H", f'"{key}: {value}"'])
    
    # Добавляем данные
    if json_data:
        # Красиво форматируем JSON
        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
        curl_parts.extend(["-d", f"'{json_str}'"])
    elif data:
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='ignore')
        curl_parts.extend(["-d", f"'{data}'"])
    
    # Добавляем URL
    curl_parts.append(f'"{url}"')
    
    # Собираем команду
    curl_command = " \\\n  ".join(curl_parts)
    
    # Формируем лог сообщение
    log_message = f"""
{'='*80}
[{datetime.now().isoformat()}] {service_name.upper()} API Request
Request ID: {request_id}
{'='*80}

{curl_command}

{'='*80}
"""
    
    # Логируем
    api_logger.info(log_message)
    
    # Асинхронно записываем в файл с полными данными
    await _write_to_file(request_id, method, url, headers, json_data, data, service_name)
    
    return request_id


async def log_api_response(
    request_id: str,
    status_code: int,
    response_data: Optional[Union[Dict[str, Any], str]] = None,
    error: Optional[str] = None,
    service_name: str = "unknown"
):
    """
    Логирует ответ API
    
    Args:
        request_id: ID запроса
        status_code: HTTP статус код
        response_data: Данные ответа
        error: Сообщение об ошибке
        service_name: Имя сервиса
    """
    
    response_str = ""
    if response_data:
        if isinstance(response_data, dict):
            response_str = json.dumps(response_data, indent=2, ensure_ascii=False)
        else:
            response_str = str(response_data)
    
    log_message = f"""
[{datetime.now().isoformat()}] {service_name.upper()} API Response
Request ID: {request_id}
Status Code: {status_code}
{'Error: ' + error if error else ''}

Response:
{response_str[:1000]}{'...' if len(response_str) > 1000 else ''}

{'='*80}
"""
    
    api_logger.info(log_message)
    
    # Асинхронно записываем полный ответ
    await _write_response_to_file(request_id, status_code, response_data, error, service_name)


async def _write_to_file(
    request_id: str,
    method: str,
    url: str,
    headers: Optional[Dict[str, str]],
    json_data: Optional[Dict[str, Any]],
    data: Optional[Union[str, bytes]],
    service_name: str
):
    """Записывает полные данные запроса в отдельный файл"""
    
    request_file = LOG_DIR / f"{request_id}_request.json"
    
    request_info = {
        "request_id": request_id,
        "timestamp": datetime.now().isoformat(),
        "service": service_name,
        "method": method,
        "url": url,
        "headers": headers,
        "json_data": json_data,
        "data": data.decode('utf-8', errors='ignore') if isinstance(data, bytes) else data
    }
    
    async with aiofiles.open(request_file, 'w') as f:
        await f.write(json.dumps(request_info, indent=2, ensure_ascii=False))


async def _write_response_to_file(
    request_id: str,
    status_code: int,
    response_data: Optional[Union[Dict[str, Any], str]],
    error: Optional[str],
    service_name: str
):
    """Записывает полные данные ответа в отдельный файл"""
    
    response_file = LOG_DIR / f"{request_id}_response.json"
    
    response_info = {
        "request_id": request_id,
        "timestamp": datetime.now().isoformat(),
        "service": service_name,
        "status_code": status_code,
        "response_data": response_data,
        "error": error
    }
    
    async with aiofiles.open(response_file, 'w') as f:
        await f.write(json.dumps(response_info, indent=2, ensure_ascii=False))


def get_curl_logs_path() -> str:
    """Возвращает путь к файлу с curl командами"""
    return str(CURL_LOG_FILE)


def get_api_logs_dir() -> str:
    """Возвращает путь к директории с логами API"""
    return str(LOG_DIR)


async def get_api_logs(
    service_name: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Получает логи API запросов с фильтрацией
    
    Args:
        service_name: Фильтр по имени сервиса
        date: Дата в формате YYYYMMDD
        limit: Максимальное количество записей
        
    Returns:
        Словарь с логами и метаданными
    """
    
    if not date:
        date = datetime.now().strftime('%Y%m%d')
    
    logs = []
    
    # Получаем список всех файлов с запросами
    request_files = list(LOG_DIR.glob("*_request.json"))
    
    # Сортируем по времени создания (новые первыми)
    request_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    for request_file in request_files[:limit]:
        try:
            # Читаем файл запроса
            async with aiofiles.open(request_file, 'r') as f:
                request_content = await f.read()
                request_data = json.loads(request_content)
            
            # Фильтруем по сервису если указан
            if service_name and request_data.get('service') != service_name:
                continue
            
            # Ищем соответствующий файл ответа
            request_id = request_data.get('request_id')
            response_file = LOG_DIR / f"{request_id}_response.json"
            
            response_data = {}
            if response_file.exists():
                try:
                    async with aiofiles.open(response_file, 'r') as f:
                        response_content = await f.read()
                        response_data = json.loads(response_content)
                except Exception as e:
                    response_data = {"error": f"Failed to read response: {str(e)}"}
            
            # Генерируем curl команду
            curl_command = generate_curl_command(
                method=request_data.get('method', 'GET'),
                url=request_data.get('url', ''),
                headers=request_data.get('headers', {}),
                json_data=request_data.get('json_data'),
                data=request_data.get('data')
            )
            
            # Объединяем данные
            log_entry = {
                "request_id": request_id,
                "timestamp": request_data.get('timestamp'),
                "service": request_data.get('service'),
                "method": request_data.get('method'),
                "url": request_data.get('url'),
                "status_code": response_data.get('status_code'),
                "error": response_data.get('error'),
                "curl_command": curl_command,
                "has_response": bool(response_data)
            }
            
            logs.append(log_entry)
            
        except Exception as e:
            # Пропускаем поврежденные файлы
            continue
    
    return {
        "logs": logs,
        "total": len(logs),
        "date": date,
        "service_filter": service_name,
        "log_directory": str(LOG_DIR)
    }


def generate_curl_command(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    data: Optional[str] = None
) -> str:
    """
    Генерирует curl команду для воспроизведения запроса
    
    Args:
        method: HTTP метод
        url: URL запроса
        headers: Заголовки
        json_data: JSON данные
        data: Raw данные
        
    Returns:
        Curl команда как строка
    """
    
    curl_parts = ["curl", "-X", method]
    
    # Добавляем заголовки
    if headers:
        for key, value in headers.items():
            # Скрываем чувствительные данные
            if key.lower() in ["authorization", "api-key", "x-api-key"]:
                masked_value = "***HIDDEN***"
                curl_parts.extend(["-H", f'"{key}: {masked_value}"'])
            else:
                curl_parts.extend(["-H", f'"{key}: {value}"'])
    
    # Добавляем данные
    if json_data:
        json_str = json.dumps(json_data, ensure_ascii=False, separators=(',', ':'))
        curl_parts.extend(["-d", f"'{json_str}'"])
    elif data:
        curl_parts.extend(["-d", f"'{data}'"])
    
    # Добавляем URL
    curl_parts.append(f'"{url}"')
    
    return " \\\n  ".join(curl_parts) 