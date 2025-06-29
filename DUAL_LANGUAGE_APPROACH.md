# Dual-Language подход для китайских транскрипций

## Обзор

Новый **Dual-Language подход** представляет собой усовершенствованную систему обработки транскрипций китайских уроков, где YandexGPT создает отдельные транскрипции на русском и китайском языках, анализирует их качество и формирует оптимальный итоговый результат.

## Проблема

**Существующий подход:**
- Получает одну транскрипцию
- Применяет простую коррекцию китайских слов
- Ограниченный контроль качества

**Результат:**
```
"Привет будет нихао, число один будет и"
↓
"Привет будет 你好 (nǐ hǎo), число один будет 一 (yī)"
```

## Решение: Dual-Language подход

**Новый подход:**
1. **Русская транскрипция** - фокус на объяснениях и структуре урока
2. **Китайская транскрипция** - фокус на правильных иероглифах и тонах
3. **Интеллектуальный анализ** - сравнение и оценка качества
4. **Оптимальная интеграция** - формирование лучшего результата

**Результат:**
```
Русская часть: "Привет, Алибек. Сегодня изучаем числа на китайском"
Китайская часть: "一 (yī) 二 (èr) 三 (sān)" 
Оптимальный результат: "Привет, Алибек. Сегодня изучаем числа на китайском. Один - 一 (yī) - первый тон, два - 二 (èr) - второй тон"
```

## Архитектура

### 1. YandexGPT Service

#### Новые методы:

```python
async def process_transcript_with_dual_approach(self, transcript: str) -> dict:
    """Обработка транскрипции с dual-language подходом"""
    
    # Получение отдельных транскрипций
    russian_transcript = await self._generate_russian_focused_transcript(transcript)
    chinese_transcript = await self._generate_chinese_focused_transcript(transcript) 
    
    # Анализ качества и совместимости
    analysis = await self._analyze_dual_transcripts(russian_transcript, chinese_transcript)
    
    # Формирование оптимального результата
    optimal_transcript = await self._create_optimal_transcript(
        transcript, russian_transcript, chinese_transcript, analysis
    )
    
    return {
        "original_transcript": transcript,
        "russian_transcript": russian_transcript,
        "chinese_transcript": chinese_transcript,
        "analysis": analysis,
        "optimal_transcript": optimal_transcript,
        "processing_method": "dual_language_analysis"
    }
```

#### Специализированные prompts:

```python
# Русский prompt
russian_prompt = """
Создай чистую русскую транскрипцию урока китайского языка.

Задачи:
1. Сохрани все объяснения и контекст на русском
2. Убери искаженные китайские слова 
3. Оставь только структуру урока и педагогические связки
4. Добавь пояснения где говорились китайские слова

Пример: "Привет будет НИХАО" → "Привет по-китайски"
"""

# Китайский prompt  
chinese_prompt = """
Создай транскрипцию только китайских слов с урока.

Задачи:
1. Замени все русские буквы на правильные иероглифы
2. Добавь пиньинь и тональные обозначения
3. Сохрани порядок слов как в уроке
4. Добавь грамматические пояснения

Пример: "НИХАО САН" → "你好 (nǐ hǎo) 三 (sān)"
"""
```

### 2. Enhanced Transcription Service

#### Новые методы:

```python
async def transcribe_lesson_with_comparison(
    self, 
    recording_id: str,
    lesson_type: str = "chinese",
    use_multiple_approaches: bool = True
) -> Dict[str, Any]:
    """Транскрипция с сравнением стандартного и dual-language подходов"""
    
    # Получение базовой транскрипции
    base_result = await self._transcribe_with_multiple_approaches(recording_id, lesson_type)
    
    # Применение обоих подходов
    standard_result = await self._apply_intelligent_post_processing(base_result.copy(), lesson_type)
    dual_language_result = await self._apply_dual_language_processing(base_result.copy(), lesson_type)
    
    # Сравнительный анализ
    comparison = await self._compare_processing_approaches(
        standard_result, dual_language_result, lesson_type
    )
    
    return {
        "approaches": {
            "standard": standard_result,
            "dual_language": dual_language_result
        },
        "comparison_analysis": comparison,
        "recommended_approach": comparison["recommended_approach"]
    }
```

### 3. API Endpoints

#### Новые endpoints:

```python
@router.post("/test-dual-language-comparison")
async def test_dual_language_comparison(
    recording_id: str,
    lesson_type: str = "chinese",
    use_multiple_approaches: bool = True
):
    """Тестирование dual-language подхода с сравнением"""
```

## Использование

### 1. Через API

#### Стандартная транскрипция:
```bash
curl -X POST "http://localhost:8000/lessons/test-enhanced-transcription" \
     -H "Content-Type: application/json" \
     -d '{
         "recording_id": "your_recording_id",
         "lesson_type": "chinese",
         "use_multiple_approaches": true
     }'
```

#### Сравнительный анализ:
```bash
curl -X POST "http://localhost:8000/lessons/test-dual-language-comparison" \
     -H "Content-Type: application/json" \
     -d '{
         "recording_id": "your_recording_id",
         "lesson_type": "chinese",
         "use_multiple_approaches": true
     }'
```

### 2. Программно

```python
from src.services.enhanced_transcription_service import EnhancedTranscriptionService

# Инициализация
service = EnhancedTranscriptionService(
    recall_api_key="your_recall_key",
    assemblyai_api_key="your_assemblyai_key"
)

# Сравнительный анализ
result = await service.transcribe_lesson_with_comparison(
    recording_id="your_recording_id",
    lesson_type="chinese"
)

# Доступ к результатам
standard_text = result["approaches"]["standard"]["text"]
dual_language_text = result["approaches"]["dual_language"]["text"]
recommended = result["recommended_approach"]
```

## Результаты сравнения

### Структура ответа:

```json
{
  "success": true,
  "recording_id": "abc123",
  "lesson_type": "chinese",
  "comparative_result": {
    "approaches": {
      "standard": {
        "method": "standard_correction",
        "text": "Стандартная коррекция...",
        "applied": true,
        "quality_metrics": {...}
      },
      "dual_language": {
        "method": "dual_language_processing", 
        "text": "Улучшенная интеграция...",
        "applied": true,
        "detailed_processing": {
          "russian_transcript": "Русская часть...",
          "chinese_transcript": "中文部分...",
          "analysis": {...},
          "optimal_transcript": "Оптимальный результат..."
        }
      }
    },
    "comparison_analysis": {
      "recommended_approach": "dual_language",
      "comparison_reasons": [
        "✓ Dual-language approach: Applied successfully",
        "✓ Chinese characters: Both approaches successful",
        "Text quality: Standard 245 chars, Dual-language 289 chars"
      ],
      "yandex_analysis": {...}
    },
    "recommended_approach": "dual_language",
    "primary_method": "dual_language"
  }
}
```

## Преимущества Dual-Language подхода

### 1. Качество транскрипции
- **Лучшая точность китайских слов** - специализированная обработка
- **Сохранение контекста** - русские объяснения остаются естественными
- **Тональные обозначения** - правильные пиньинь с тонами

### 2. Гибкость обработки
- **Адаптивность** - подход адаптируется к типу урока
- **Масштабируемость** - легко добавить новые языки
- **Контроль качества** - автоматическая оценка результатов

### 3. Аналитика
- **Детальная диагностика** - понимание процесса обработки
- **Сравнительный анализ** - выбор лучшего подхода
- **Метрики качества** - количественная оценка улучшений

## Сравнение подходов

| Аспект | Стандартный | Dual-Language |
|--------|-------------|---------------|
| **Скорость** | Быстро | Медленнее |
| **Точность китайского** | Базовая | Высокая |
| **Контекст русского** | Сохраняется | Улучшается |
| **Аналитика** | Минимальная | Подробная |
| **Настраиваемость** | Ограниченная | Высокая |
| **Тональность** | Базовая | Точная |

## Тестирование

### Запуск тестов:

```bash
# Демонстрация подхода
python test_dual_language_approach.py

# Интеграционное тестирование
python test_chinese_correction.py
```

### Примеры результатов:

**Входная транскрипция:**
```
"Привет, Алибек. Числа. Один будет И. Два АР. Три САН."
```

**Стандартный подход:**
```
"привет, алибек. числа. один будет 一 (yī). два 二 (èr). три 三 (sān)."
```

**Dual-Language подход:**
```
"Привет, Алибек. Сегодня изучаем числа на китайском. Один - 一 (yī) первый тон, два - 二 (èr) второй тон, три - 三 (sān) третий тон."
```

## Конфигурация

### Environment Variables:

```env
# YandexGPT настройки для dual-language
YANDEX_FOLDER_ID=your_folder_id
YANDEX_API_KEY=your_api_key

# Настройки dual-language обработки
ENABLE_DUAL_LANGUAGE=true
DUAL_LANGUAGE_CONFIDENCE_THRESHOLD=0.8
DUAL_LANGUAGE_TIMEOUT=30
```

### Настройки в коде:

```python
# В enhanced_transcription_service.py
dual_language_config = {
    "enabled": True,
    "confidence_threshold": 0.8,
    "timeout": 30,
    "fallback_to_standard": True
}
```

## Мониторинг и логирование

### Логи обработки:

```
[INFO] Starting dual-language transcript processing
[INFO] Russian transcript generated: 156 characters
[INFO] Chinese transcript generated: 45 characters  
[INFO] Analysis completed with confidence: 0.92
[INFO] Optimal transcript created: 201 characters
[INFO] Dual-language processing successfully applied
```

### Метрики:

- **Processing time**: время обработки dual-language vs standard
- **Quality scores**: оценка качества каждого подхода
- **Success rate**: процент успешных обработок
- **Character improvements**: увеличение качества текста

## Развитие

### Планируемые улучшения:

1. **Поддержка других языков** - арабский, корейский, японский
2. **Кэширование результатов** - ускорение повторных запросов  
3. **ML-модель выбора** - автоматический выбор подхода
4. **Batch processing** - обработка множественных транскрипций

### Настройка под новые языки:

```python
# Добавление поддержки японского
japanese_config = {
    "script_range": ("\u3040", "\u309f"),  # Hiragana
    "prompt_template": "japanese_lesson_prompt.txt",
    "tone_support": False,
    "romanization": "romaji"
}
``` 