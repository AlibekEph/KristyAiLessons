# API Documentation - KristyLessonRecords

## Обзор

KristyLessonRecords предоставляет REST API для автоматической записи и обработки онлайн-уроков китайского и английского языков.

## Swagger UI

После запуска сервиса документация доступна по адресам:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Аутентификация

В текущей версии API не требует аутентификации. В production рекомендуется добавить JWT или API ключи.

## Базовый URL

```
http://localhost:8000
```

## Эндпоинты

### 1. Начать запись урока

**POST** `/lessons/record`

Запускает процесс записи онлайн-урока.

**Тело запроса:**
```json
{
  "meeting_url": "https://zoom.us/j/1234567890",
  "lesson_type": "chinese",
  "student_id": "student_123",
  "teacher_id": "teacher_456",
  "student_level": "beginner",
  "metadata": {
    "topic": "Базовые приветствия",
    "lesson_number": 1
  }
}
```

**Параметры:**
- `meeting_url` (string, обязательный) - URL встречи (Zoom, Google Meet и т.д.)
- `lesson_type` (string, обязательный) - Тип урока: "chinese" или "english"
- `student_id` (string, опциональный) - ID студента
- `teacher_id` (string, опциональный) - ID преподавателя
- `student_level` (string, опциональный) - Уровень: "beginner", "intermediate", "advanced"
- `metadata` (object, опциональный) - Дополнительные данные

**Ответ (200 OK):**
```json
{
  "id": "lesson_1234567890.123",
  "status": "recording",
  "meeting_url": "https://zoom.us/j/1234567890",
  "lesson_type": "chinese",
  "created_at": "2024-01-20T10:30:00",
  "transcript_available": false,
  "materials_available": false
}
```

**Статусы урока:**
- `recording` - Идёт запись
- `transcribing` - Создаётся транскрипция
- `processing` - AI обрабатывает материалы
- `completed` - Обработка завершена
- `failed` - Произошла ошибка

### 2. Получить информацию об уроке

**GET** `/lessons/{lesson_id}`

Возвращает текущий статус и информацию об уроке.

**Параметры пути:**
- `lesson_id` (string) - ID урока

**Ответ (200 OK):**
```json
{
  "id": "lesson_1234567890.123",
  "status": "completed",
  "meeting_url": "https://zoom.us/j/1234567890",
  "lesson_type": "chinese",
  "created_at": "2024-01-20T10:30:00",
  "transcript_available": true,
  "materials_available": true
}
```

### 3. Получить транскрипцию

**GET** `/lessons/{lesson_id}/transcript`

Возвращает полную транскрипцию урока.

**Параметры пути:**
- `lesson_id` (string) - ID урока

**Ответ (200 OK):**
```json
{
  "id": "transcript_123",
  "text": "Преподаватель: Привет! Сегодня мы изучаем числа. На китайском один будет 一 (yī), два - 二 (èr)...",
  "segments": [
    {
      "text": "Привет! Сегодня мы изучаем числа.",
      "start": 0.0,
      "end": 3.5,
      "speaker": "Teacher"
    },
    {
      "text": "На китайском один будет 一 (yī)",
      "start": 3.5,
      "end": 6.2,
      "speaker": "Teacher"
    }
  ],
  "language": "ru",
  "duration": 1800.0
}
```

### 4. Получить учебные материалы

**GET** `/lessons/{lesson_id}/materials`

Возвращает сгенерированные AI учебные материалы.

**Параметры пути:**
- `lesson_id` (string) - ID урока

**Ответ (200 OK):**
```json
{
  "lesson_id": "lesson_1234567890.123",
  "original_transcript": "Привет! Сегодня мы изучаем числа. На китайском один будет и, два - ар...",
  "corrected_transcript": "Привет! Сегодня мы изучаем числа. На китайском один будет 一 (yī), два - 二 (èr)...",
  "summary": "## Основная тема урока\n\nЧисла от 1 до 10 на китайском языке\n\n## Изученная лексика\n\n- 一 (yī) - один\n- 二 (èr) - два\n- 三 (sān) - три\n\n## Грамматические конструкции\n\nИспользование счётных слов...",
  "homework": "## Упражнения на новую лексику\n\n1. Напишите числа от 1 до 10 иероглифами\n2. Запишите аудио с произношением всех чисел\n3. Составьте 5 предложений используя числа\n\n## Письменное задание\n\nНапишите короткий диалог...",
  "notes": "На уроке изучили базовые числа от 1 до 10. Особое внимание уделили правильному произношению тонов. Студент хорошо усвоил материал.",
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
    },
    {
      "word": "三",
      "pinyin": "sān",
      "translation": "три",
      "example": "三天 (sān tiān) - три дня"
    }
  ],
  "created_at": "2024-01-20T11:00:00"
}
```

## Примеры использования

### Python

```python
import requests
import time

# Базовый URL
BASE_URL = "http://localhost:8000"

# 1. Начать запись урока
response = requests.post(
    f"{BASE_URL}/lessons/record",
    json={
        "meeting_url": "https://zoom.us/j/1234567890",
        "lesson_type": "chinese",
        "student_id": "student_123",
        "student_level": "beginner",
        "metadata": {
            "topic": "Числа от 1 до 10"
        }
    }
)

lesson = response.json()
lesson_id = lesson["id"]
print(f"Начата запись урока: {lesson_id}")

# 2. Проверять статус
while True:
    response = requests.get(f"{BASE_URL}/lessons/{lesson_id}")
    lesson = response.json()
    
    print(f"Статус: {lesson['status']}")
    
    if lesson["status"] == "completed":
        break
    elif lesson["status"] == "failed":
        print("Ошибка обработки")
        break
    
    time.sleep(30)  # Проверять каждые 30 секунд

# 3. Получить транскрипцию
if lesson["transcript_available"]:
    response = requests.get(f"{BASE_URL}/lessons/{lesson_id}/transcript")
    transcript = response.json()
    print(f"Транскрипция: {transcript['text'][:200]}...")

# 4. Получить учебные материалы
if lesson["materials_available"]:
    response = requests.get(f"{BASE_URL}/lessons/{lesson_id}/materials")
    materials = response.json()
    
    print("\n=== КОНСПЕКТ ===")
    print(materials["summary"])
    
    print("\n=== ДОМАШНЕЕ ЗАДАНИЕ ===")
    print(materials["homework"])
    
    print("\n=== СЛОВАРЬ ===")
    for word in materials["vocabulary"]:
        print(f"{word['word']} ({word['pinyin']}) - {word['translation']}")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

async function recordAndProcessLesson() {
    try {
        // 1. Начать запись
        const recordResponse = await axios.post(`${BASE_URL}/lessons/record`, {
            meeting_url: 'https://zoom.us/j/1234567890',
            lesson_type: 'chinese',
            student_id: 'student_123',
            student_level: 'beginner',
            metadata: {
                topic: 'Числа от 1 до 10'
            }
        });

        const lessonId = recordResponse.data.id;
        console.log(`Начата запись урока: ${lessonId}`);

        // 2. Ждать завершения обработки
        let lesson;
        do {
            const statusResponse = await axios.get(`${BASE_URL}/lessons/${lessonId}`);
            lesson = statusResponse.data;
            console.log(`Статус: ${lesson.status}`);
            
            if (lesson.status === 'failed') {
                throw new Error('Ошибка обработки урока');
            }
            
            if (lesson.status !== 'completed') {
                await new Promise(resolve => setTimeout(resolve, 30000)); // 30 секунд
            }
        } while (lesson.status !== 'completed');

        // 3. Получить материалы
        if (lesson.materials_available) {
            const materialsResponse = await axios.get(`${BASE_URL}/lessons/${lessonId}/materials`);
            const materials = materialsResponse.data;
            
            console.log('\n=== СЛОВАРЬ ===');
            materials.vocabulary.forEach(word => {
                console.log(`${word.word} (${word.pinyin}) - ${word.translation}`);
            });
        }

    } catch (error) {
        console.error('Ошибка:', error.message);
    }
}

recordAndProcessLesson();
```

### cURL

```bash
# 1. Начать запись урока
curl -X POST http://localhost:8000/lessons/record \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_url": "https://zoom.us/j/1234567890",
    "lesson_type": "chinese",
    "student_level": "beginner"
  }'

# 2. Проверить статус
curl http://localhost:8000/lessons/lesson_1234567890.123

# 3. Получить транскрипцию
curl http://localhost:8000/lessons/lesson_1234567890.123/transcript

# 4. Получить учебные материалы
curl http://localhost:8000/lessons/lesson_1234567890.123/materials
```

## Обработка ошибок

API использует стандартные HTTP коды ответов:

- `200 OK` - Успешный запрос
- `404 Not Found` - Ресурс не найден
- `422 Unprocessable Entity` - Ошибка валидации данных
- `500 Internal Server Error` - Внутренняя ошибка сервера

Пример ошибки:
```json
{
  "detail": "Lesson not found"
}
```

## Webhook интеграция

Сервис использует webhooks для асинхронной обработки:

1. **Recall.ai webhooks** - уведомления о статусе записи
2. **AssemblyAI webhooks** - уведомления о готовности транскрипции

Эти эндпоинты используются внутренне и не предназначены для прямого вызова.

## Рекомендации

1. **Polling vs Webhooks**: Для production рекомендуется реализовать собственные webhooks или WebSocket для уведомлений вместо polling.

2. **Таймауты**: Обработка урока может занять до 30 минут после его окончания.

3. **Повторные попытки**: При получении ошибки 500, рекомендуется повторить запрос через некоторое время.

4. **Хранение данных**: Материалы хранятся неограниченное время. Рекомендуется реализовать политику удаления старых данных.

### 🔍 Debug API

#### GET /debug/api-logs
Просмотр логов API запросов к внешним сервисам с возможностью воспроизведения через curl.

**Параметры запроса:**
- `service` (optional): Фильтр по сервису (recall, assemblyai, yandexgpt)
- `date` (optional): Дата в формате YYYYMMDD
- `limit` (optional): Максимальное количество записей (по умолчанию 50)

**Пример запроса:**
```bash
curl -X GET "http://localhost:8000/debug/api-logs?service=recall&limit=10"
```

**Пример ответа:**
```json
{
  "logs": [
    {
      "request_id": "recall_20240120_143022_123456",
      "timestamp": "2024-01-20T14:30:22.123456",
      "service": "recall",
      "method": "POST",
      "url": "https://us-west-2.recall.ai/api/v1/bot",
      "status_code": 403,
      "error": "Forbidden: Invalid API key",
      "curl_command": "curl -X POST \\\n  -H \"Authorization: ***HIDDEN***\" \\\n  -H \"Content-Type: application/json\" \\\n  -d '{\"meeting_url\":\"https://zoom.us/j/123\"}' \\\n  \"https://us-west-2.recall.ai/api/v1/bot\"",
      "has_response": true
    }
  ],
  "total": 1,
  "service_filter": "recall",
  "log_directory": "/app/logs/api_requests"
}
```

**Использование для отладки:**
1. Скопируйте `curl_command` из ответа
2. Замените `***HIDDEN***` на реальный API ключ
3. Выполните команду для воспроизведения запроса

**Логи также доступны в файлах:**
- `/app/logs/api_requests/curl_commands_YYYYMMDD.log` - curl команды
- `/app/logs/api_requests/{request_id}_request.json` - детали запроса
- `/app/logs/api_requests/{request_id}_response.json` - ответ API 