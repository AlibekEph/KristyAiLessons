#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции с Recall.ai
Согласно документации: https://docs.recall.ai/reference/bot_create
"""

import asyncio
import os
import json
from dotenv import load_dotenv
import aiohttp

# Загружаем переменные окружения
load_dotenv()

async def test_recall_api():
    """Тестируем создание бота согласно документации Recall.ai"""
    
    api_key = os.getenv("RECALL_API_KEY")
    if not api_key or api_key == "your_recall_api_key_here":
        print("❌ Ошибка: Установите реальный RECALL_API_KEY в файле .env")
        return
    
    # Параметры согласно документации
    base_url = "https://us-west-2.recall.ai/api/v1"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    # Минимальный payload для теста
    # В документации указано, что meeting_url обязателен
    payload = {
        "meeting_url": "https://zoom.us/j/1234567890",  # Тестовый URL
        "bot_name": "Test Bot",
        # Дополнительные параметры согласно нашей реализации
        "transcription_options": {
            "provider": "assembly_ai"
        },
        "recording": {
            "mode": "speaker_view"
        }
    }
    
    print("📡 Отправляем запрос на Recall.ai API...")
    print(f"URL: {base_url}/bot/")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{base_url}/bot/",
                json=payload,
                headers=headers
            ) as response:
                status = response.status
                text = await response.text()
                
                print(f"\n📊 Статус ответа: {status}")
                
                if status == 200 or status == 201:
                    data = json.loads(text)
                    print("✅ Успешно создан бот!")
                    print(f"Ответ: {json.dumps(data, indent=2)}")
                    
                    # Если бот создан, попробуем его удалить
                    if "id" in data:
                        bot_id = data["id"]
                        print(f"\n🗑️  Удаляем тестового бота {bot_id}...")
                        
                        # Отправляем команду покинуть звонок
                        async with session.post(
                            f"{base_url}/bot/{bot_id}/leave_call",
                            headers=headers
                        ) as delete_response:
                            if delete_response.status == 200:
                                print("✅ Бот успешно удален")
                else:
                    print(f"❌ Ошибка: {text}")
                    
                    # Проверяем типичные ошибки
                    if status == 401:
                        print("🔑 Проблема с авторизацией. Проверьте API ключ.")
                    elif status == 403:
                        print("🚫 Доступ запрещен. Возможно, API ключ неверный или не имеет прав.")
                    elif status == 429:
                        print("⏱️  Превышен лимит запросов (60 запросов в минуту).")
                    
        except Exception as e:
            print(f"❌ Ошибка при выполнении запроса: {e}")


async def test_our_service():
    """Тестируем наш сервис"""
    print("\n\n🧪 Тестируем наш сервис...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Проверяем health check
            async with session.get("http://localhost:8000/") as response:
                if response.status == 200:
                    print("✅ Наш сервис работает")
                else:
                    print("❌ Наш сервис не отвечает")
                    return
                    
            # Пробуем создать запись
            payload = {
                "meeting_url": "https://zoom.us/j/1234567890",
                "lesson_type": "chinese",
                "student_id": "test_student",
                "metadata": {
                    "test": True
                }
            }
            
            async with session.post(
                "http://localhost:8000/lessons/record",
                json=payload
            ) as response:
                status = response.status
                text = await response.text()
                
                print(f"\n📊 Статус ответа от нашего сервиса: {status}")
                print(f"Ответ: {text}")
                
                if status == 500 and "403" in text:
                    print("\n⚠️  Наш сервис работает, но Recall.ai возвращает 403 (Forbidden)")
                    print("Это ожидаемо с тестовым API ключом.")
                    
        except Exception as e:
            print(f"❌ Ошибка при тестировании нашего сервиса: {e}")


async def main():
    print("🔍 Тестирование интеграции с Recall.ai\n")
    
    # Тест 1: Прямой вызов Recall.ai API
    await test_recall_api()
    
    # Тест 2: Вызов через наш сервис
    await test_our_service()


if __name__ == "__main__":
    asyncio.run(main()) 