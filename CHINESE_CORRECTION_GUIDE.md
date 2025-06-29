# Руководство по коррекции китайских транскрипций с YandexGPT

## Обзор

Система Enhanced Transcription теперь интегрирована с YandexGPT для автоматической коррекции китайских слов в транскрипциях. Это решает проблему, когда китайские слова записываются кириллицей вместо иероглифов.

## Как это работает

### Проблема
Когда система транскрипции обрабатывает урок китайского языка, китайские слова часто записываются русскими буквами:
```
"Привет будет НИХАО, а как дела - НИХАО МА"
```

### Решение
YandexGPT автоматически преобразует русские буквы в правильные китайские иероглифы:
```
"Привет будет 你好 (nǐ hǎo), а как дела - 你好吗 (nǐ hǎo ma)"
```

## Настройка

### 1. Переменные окружения
Добавьте в ваш `.env` файл:
```env
YANDEX_FOLDER_ID=your_folder_id
YANDEX_API_KEY=your_api_key
YANDEX_MODEL_URI=gpt://your_folder_id/yandexgpt-lite  # опционально
```

### 2. Получение ключей Yandex Cloud
1. Создайте аккаунт в [Yandex Cloud](https://cloud.yandex.ru/)
2. Создайте каталог (folder)
3. Получите API ключ в разделе "Сервисные аккаунты"
4. Folder ID можно найти в URL консоли облака

## Использование

### Автоматическая коррекция
Коррекция автоматически применяется для всех китайских уроков при использовании Enhanced Transcription Service:

```python
from src.services.enhanced_transcription_service import EnhancedTranscriptionService

service = EnhancedTranscriptionService(recall_api_key, assemblyai_api_key)

# Коррекция применится автоматически для lesson_type="chinese"
result = await service.transcribe_lesson(
    recording_id="your_recording_id",
    lesson_type="chinese"
)

# Проверить, была ли применена коррекция
if result.get("yandexgpt_correction_applied"):
    print("✅ YandexGPT коррекция применена")
    print(f"Исправленный текст: {result['text']}")
```

### Ручная коррекция
Также можно использовать YandexGPT напрямую:

```python
from src.services.yandexgpt_service import YandexGPTService

yandex_service = YandexGPTService(
    folder_id="your_folder_id",
    api_key="your_api_key"
)

original_text = "Один будет И, два будет АР, три будет САН"
corrected_text = await yandex_service._correct_chinese_transcript(original_text)
print(corrected_text)
# Результат: "Один будет 一 (yī), два будет 二 (èr), три будет 三 (sān)"
```

## Тестирование

### Запуск тестов
```bash
cd KristyRecords/KristyAiLessons
python test_chinese_correction.py
```

### Через API
```bash
curl -X POST "http://localhost:8000/lessons/test-lesson-id/test-enhanced-transcription" \
  -H "Content-Type: application/json"
```

## Примеры коррекции

### Числа
**До:** "Один будет И, два АР, три САН"
**После:** "Один будет 一 (yī), два 二 (èr), три 三 (sān)"

### Приветствия
**До:** "Привет это НИХАО, как дела НИХАО МА"
**После:** "Привет это 你好 (nǐ hǎo), как дела 你好吗 (nǐ hǎo ma)"

### Базовые фразы
**До:** "Меня зовут ВО ЦЗЯО, до свидания ЦЗАЙЦЗЯНЬ"
**После:** "Меня зовут 我叫 (wǒ jiào), до свидания 再见 (zài jiàn)"

## Мониторинг и отладка

### Логи
Система записывает подробные логи коррекции:
```
INFO: Applying YandexGPT Chinese correction to transcript
INFO: YandexGPT correction successfully applied
```

### Метрики результата
```python
result = await service.transcribe_lesson(recording_id, "chinese")

# Проверка статуса коррекции
print(f"Коррекция применена: {result.get('yandexgpt_correction_applied')}")
print(f"Ошибка коррекции: {result.get('yandexgpt_correction_error')}")
```

### Валидация
Система автоматически проверяет:
- Что коррекция не вернула пустой результат
- Что в тексте появились китайские иероглифы
- Что длина текста разумная

## Ограничения

### Поддерживаемые языки
- ✅ Русский → Китайский
- ✅ Смешанный русский/китайский контент
- ❌ Другие языковые пары (планируется)

### Точность
- Высокая точность для базовой лексики
- Может потребоваться ручная проверка для специализированной терминологии
- Лучше работает с контекстом урока

### Производительность
- Дополнительная задержка ~1-3 секунды на коррекцию
- Кеширование не реализовано (планируется)

## Устранение неполадок

### YandexGPT недоступен
```python
# Система автоматически продолжит без коррекции
if not result.get('yandexgpt_correction_applied'):
    print("Коррекция не применена, используется оригинальный текст")
```

### Ошибки API
```python
if result.get('yandexgpt_correction_error'):
    print(f"Ошибка API: {result['yandexgpt_correction_error']}")
```

### Проверка конфигурации
```bash
# Проверить переменные окружения
echo $YANDEX_FOLDER_ID
echo $YANDEX_API_KEY
```

## Дальнейшее развитие

### Планируемые улучшения
- [ ] Кеширование результатов коррекции
- [ ] Поддержка других языковых пар
- [ ] Обучение на специализированной терминологии
- [ ] Интеграция с пользовательским словарем
- [ ] Пакетная обработка для оптимизации

### Обратная связь
Если вы заметили ошибки в коррекции или у вас есть предложения по улучшению, создайте issue в репозитории с примерами некорректной коррекции. 