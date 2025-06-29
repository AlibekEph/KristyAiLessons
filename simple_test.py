#!/usr/bin/env python3
"""
Простой тест Recall.ai API без зависимостей
"""

import json
import urllib.request
import urllib.parse

def test_recall_api():
    """Тестируем API Recall.ai с минимальным запросом"""
    
    # Параметры
    api_key = "1381701c07cf6c2867198b6f416d5a0933158997"  # Из .env файла
    base_url = "https://us-west-2.recall.ai/api/v1"
    
    # Минимальный payload из документации
    payload = {
        "meeting_url": "https://meet.google.com/hmn-wtbp-myh",
        "bot_name": "Test Bot",
        "recording_config": {
            "transcript": {
                "provider": {
                    "meeting_captions": {}
                }
            }
        }
    }
    
    # Подготавливаем запрос
    data = json.dumps(payload).encode('utf-8')
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    print("📡 Отправляем запрос на Recall.ai API...")
    print(f"URL: {base_url}/bot")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Создаем запрос
        req = urllib.request.Request(
            f"{base_url}/bot",
            data=data,
            headers=headers,
            method='POST'
        )
        
        # Отправляем запрос
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            
            print(f"\n✅ Статус: {status}")
            print(f"Ответ: {json.dumps(json.loads(body), indent=2)}")
            
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode('utf-8')
        
        print(f"\n❌ Ошибка {status}")
        print(f"Ответ: {body}")
        
        # Пытаемся распарсить JSON
        try:
            error_data = json.loads(body)
            print(f"Детали ошибки: {json.dumps(error_data, indent=2)}")
        except:
            print("Не удалось распарсить ответ как JSON")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_recall_api() 