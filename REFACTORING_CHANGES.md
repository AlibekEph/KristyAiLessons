# Рефакторинг и новые возможности

## Обзор изменений

В рамках этого обновления была проведена реорганизация кода и добавлены новые API эндпоинты для получения уроков с пагинацией и фильтрацией.

## 🗂️ Новая структура проекта

### Модели (models/)
Модели разделены на отдельные файлы для лучшей читаемости:

```
src/models/
├── __init__.py          # Экспорт всех моделей
├── base.py             # Базовый класс SQLAlchemy
├── lesson.py           # Модель урока
├── transcript.py       # Модель транскрипции
└── materials.py        # Модель учебных материалов
```

### Фильтры (filters/)
Новая система фильтрации для гибкой работы с данными:

```
src/filters/
├── __init__.py          # Экспорт фильтров
└── lesson_filters.py    # Фильтры для уроков
```

### Контроллеры (controllers/)
Бизнес-логика вынесена в контроллеры:

```
src/controllers/
├── __init__.py          # Экспорт контроллеров
└── lesson_controller.py # Контроллер для уроков
```

## 🚀 Новые API эндпоинты

### 1. GET /lessons - Список уроков с пагинацией

**Возможности:**
- Пагинация (page, page_size)
- Сортировка по любому полю (order_by, order_direction)
- Множественные фильтры
- Поиск по тексту
- Фильтрация по наличию связанных данных

**Пример запроса:**
```bash
GET /lessons?page=1&page_size=10&status=completed&lesson_type=chinese&has_materials=true
```

**Ответ:**
```json
{
  "items": [...],
  "meta": {
    "page": 1,
    "page_size": 10,
    "total_items": 25,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  }
}
```

### 2. GET /lessons/statistics - Статистика уроков

**Возможности:**
- Общее количество уроков
- Распределение по статусам
- Распределение по типам
- Счетчики наличия транскрипций и материалов
- Фильтрация статистики

**Пример ответа:**
```json
{
  "total_lessons": 50,
  "status_distribution": {
    "completed": 35,
    "processing": 5,
    "recording": 3,
    "failed": 2
  },
  "type_distribution": {
    "chinese": 30,
    "english": 20
  },
  "with_transcript": 40,
  "with_materials": 35
}
```

## 📋 Доступные фильтры

### Статус и тип
- `status` - Один статус
- `statuses` - Несколько статусов
- `lesson_type` - Один тип урока
- `lesson_types` - Несколько типов

### Пользователи
- `student_id` - ID студента
- `teacher_id` - ID преподавателя

### Даты
- `created_after` / `created_before` - По дате создания
- `started_after` / `started_before` - По дате начала

### Поиск и наличие данных
- `search` - Поиск по URL и метаданным
- `has_transcript` - Есть ли транскрипция
- `has_materials` - Есть ли учебные материалы

## 🔧 Технические улучшения

### 1. Система фильтрации
- Класс `LessonFilter` для применения фильтров к запросам
- Pydantic модель `LessonFilterParams` для валидации
- Поддержка сложных условий (OR, LIKE, EXISTS)

### 2. Контроллеры
- Класс `LessonController` с бизнес-логикой
- Методы для пагинации, фильтрации, статистики
- Eager loading для оптимизации запросов

### 3. Схемы данных
- Новые Pydantic схемы для пагинации
- Генерик `PaginatedResponse` для переиспользования
- Enum'ы для валидации статусов и типов

### 4. Обратная совместимость
- Старый файл `models.py` импортирует из новой структуры
- Существующие CRUD функции обновлены
- Все старые API продолжают работать

## 📚 Использование

### Python пример
```python
import requests

# Получить первые 10 завершенных уроков китайского
response = requests.get("http://localhost:8000/lessons", params={
    "page": 1,
    "page_size": 10,
    "status": "completed",
    "lesson_type": "chinese",
    "order_by": "created_at",
    "order_direction": "desc"
})

data = response.json()
print(f"Найдено {data['meta']['total_items']} уроков")

# Получить статистику за последний месяц
from datetime import datetime, timedelta
month_ago = datetime.now() - timedelta(days=30)

response = requests.get("http://localhost:8000/lessons/statistics", params={
    "created_after": month_ago.isoformat()
})

stats = response.json()
print(f"Уроков за месяц: {stats['total_lessons']}")
```

### cURL примеры
```bash
# Список с фильтрами
curl "http://localhost:8000/lessons?status=completed&lesson_type=chinese&page=1&page_size=10"

# Поиск уроков
curl "http://localhost:8000/lessons?search=zoom&has_materials=true"

# Статистика
curl "http://localhost:8000/lessons/statistics?lesson_type=chinese"
```

## 🧪 Тестирование

Создан тестовый файл `test_new_api.py` для проверки новых эндпоинтов:

```bash
python3 test_new_api.py
```

Также создан `check_imports.py` для проверки корректности импортов:

```bash
python3 check_imports.py
```

## 📖 Документация

- Обновлена `API_DOCUMENTATION.md` с новыми эндпоинтами
- Добавлены примеры использования
- Swagger UI автоматически включает новые API

## 🔄 Миграция

Для применения изменений в существующем проекте:

1. Скопировать новые папки: `models/`, `controllers/`, `filters/`
2. Обновить `schemas.py`, `crud.py`, `database.py`
3. Добавить новый роутер `routers/lessons/get_list.py`
4. Обновить `routers/lessons_api.py`

Все изменения обратно совместимы - существующий код продолжит работать.

## ✨ Преимущества

1. **Производительность**: Eager loading, оптимизированные запросы
2. **Гибкость**: Мощная система фильтрации и пагинации
3. **Масштабируемость**: Разделение на слои (модели, контроллеры, фильтры)
4. **Удобство**: Богатые возможности поиска и статистики
5. **Качество кода**: Лучшая организация, читаемость, переиспользование 