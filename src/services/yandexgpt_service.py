"""YandexGPT AI processor implementation"""

import aiohttp
import json
import re
from typing import Dict, Optional, Any, List
from datetime import datetime
import logging

from ..interfaces.ai_processor import (
    AIProcessorInterface,
    AIProcessingRequest,
    LessonMaterials
)
from ..utils.api_logger import log_api_request, log_api_response


logger = logging.getLogger(__name__)


class YandexGPTService(AIProcessorInterface):
    """YandexGPT service implementation"""
    
    def __init__(
        self,
        folder_id: str,
        api_key: str,
        model_uri: Optional[str] = None
    ):
        self.folder_id = folder_id
        self.api_key = api_key
        self.model_uri = model_uri or f"gpt://{folder_id}/yandexgpt-lite"
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {api_key}",
            "x-folder-id": folder_id
        }
    
    async def process_lesson(
        self,
        request: AIProcessingRequest
    ) -> LessonMaterials:
        """Process lesson transcript and generate materials"""
        
        # First, correct the transcript
        corrected_transcript = await self.correct_multilingual_transcript(
            request.transcript,
            target_languages=["zh"] if request.lesson_type == "chinese" else ["en"]
        )
        
        # Generate summary
        summary = await self.generate_summary(
            corrected_transcript,
            request.lesson_type,
            request.student_level
        )
        
        # Generate homework
        homework = await self.generate_homework(
            corrected_transcript,
            request.lesson_type,
            request.student_level
        )
        
        # Extract vocabulary
        vocabulary = await self.extract_vocabulary(
            corrected_transcript,
            request.lesson_type
        )
        
        # Generate brief notes
        notes = await self._generate_notes(
            corrected_transcript,
            request.lesson_type
        )
        
        return LessonMaterials(
            lesson_id=request.metadata.get("lesson_id", ""),
            original_transcript=request.transcript,
            corrected_transcript=corrected_transcript,
            summary=summary,
            homework=homework,
            notes=notes,
            key_vocabulary=vocabulary,
            metadata=request.metadata
        )
    
    async def correct_multilingual_transcript(
        self,
        transcript: str,
        source_language: str = "ru",
        target_languages: Optional[List[str]] = None
    ) -> str:
        """Correct multilingual transcript by adding proper characters and pinyin"""
        
        if not target_languages:
            return transcript
        
        prompt = f"""Исправь транскрипцию урока, добавив правильное написание на целевом языке.

Правила:
1. Русский текст оставляй без изменений
2. Для китайского: замени транслитерацию на иероглифы с пиньинь в скобках
3. Для английского: исправь неправильно транскрибированные английские слова
4. Сохрани структуру и смысл текста

Пример для китайского:
Вход: "Привет будет Нихао, а как дела - Нихао ма"
Выход: "Привет будет 你好 (nǐ hǎo), а как дела - 你好吗 (nǐ hǎo ma)"

Транскрипция для исправления:
{transcript}

Исправленная транскрипция:"""

        response = await self._make_request(prompt)
        return response.strip()
    
    async def generate_summary(
        self,
        transcript: str,
        lesson_type: str,
        student_level: Optional[str] = None
    ) -> str:
        """Generate lesson summary"""
        
        level_text = f"(уровень: {student_level})" if student_level else ""
        
        prompt = f"""Создай структурированный конспект урока {lesson_type} языка {level_text}.

Формат конспекта:
1. **Основная тема урока**
2. **Изученная лексика** (слова/фразы с переводом и примерами)
3. **Грамматические конструкции** (с объяснениями и примерами)
4. **Ключевые моменты** (важные объяснения преподавателя)
5. **Практические упражнения** (что делали на уроке)

Транскрипция урока:
{transcript}

Конспект:"""

        response = await self._make_request(prompt)
        return response.strip()
    
    async def generate_homework(
        self,
        transcript: str,
        lesson_type: str,
        student_level: Optional[str] = None,
        previous_homework: Optional[str] = None
    ) -> str:
        """Generate homework based on lesson content"""
        
        level_text = f"(уровень: {student_level})" if student_level else ""
        prev_hw_text = f"\n\nПредыдущее домашнее задание:\n{previous_homework}" if previous_homework else ""
        
        prompt = f"""Создай домашнее задание по уроку {lesson_type} языка {level_text}.

Домашнее задание должно включать:
1. **Упражнения на новую лексику** (минимум 5 заданий)
2. **Грамматические упражнения** (минимум 3 задания)
3. **Задания на говорение** (2-3 темы для практики)
4. **Письменное задание** (короткое сочинение или диалог)
5. **Рекомендации по повторению**

Учитывай пройденный материал и делай задания практичными.{prev_hw_text}

Транскрипция урока:
{transcript}

Домашнее задание:"""

        response = await self._make_request(prompt)
        return response.strip()
    
    async def extract_vocabulary(
        self,
        transcript: str,
        lesson_type: str
    ) -> List[Dict[str, str]]:
        """Extract key vocabulary from lesson"""
        
        prompt = f"""Извлеки ключевую лексику из урока {lesson_type} языка.

Формат ответа - JSON массив объектов:
[
  {{
    "word": "слово на изучаемом языке",
    "pinyin": "пиньинь (только для китайского)",
    "translation": "перевод на русский",
    "example": "пример использования"
  }}
]

Извлеки только новые слова и выражения, которые объяснялись на уроке.

Транскрипция:
{transcript}

JSON:"""

        response = await self._make_request(prompt)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                vocabulary = json.loads(json_match.group())
                # Ensure correct format
                formatted_vocab = []
                for item in vocabulary:
                    vocab_item = {
                        "word": item.get("word", ""),
                        "translation": item.get("translation", "")
                    }
                    if lesson_type == "chinese" and "pinyin" in item:
                        vocab_item["pinyin"] = item["pinyin"]
                    if "example" in item:
                        vocab_item["example"] = item["example"]
                    formatted_vocab.append(vocab_item)
                return formatted_vocab
        except json.JSONDecodeError:
            logger.error(f"Failed to parse vocabulary JSON: {response}")
        
        return []
    
    async def _generate_notes(
        self,
        transcript: str,
        lesson_type: str
    ) -> str:
        """Generate brief lesson notes"""
        
        prompt = f"""Создай краткое описание урока {lesson_type} языка (3-5 предложений).

Опиши:
- Что изучали на уроке
- Основные достижения
- На что обратить внимание при повторении

Транскрипция:
{transcript}

Краткое описание:"""

        response = await self._make_request(prompt)
        return response.strip()
    
    async def _make_request(self, prompt: str, temperature: float = 0.3) -> str:
        """Make request to YandexGPT API"""
        
        payload = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": 2000
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Ты - опытный преподаватель языков, помогающий создавать учебные материалы."
                },
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }
        
        # Логируем API запрос
        request_id = await log_api_request(
            method="POST",
            url=self.base_url,
            headers=self.headers,
            json_data=payload,
            service_name="yandexgpt"
        )
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.base_url,
                    json=payload,
                    headers=self.headers
                ) as response:
                    status_code = response.status
                    data = await response.json()
                    
                    # Логируем ответ
                    await log_api_response(
                        request_id=request_id,
                        status_code=status_code,
                        response_data=data,
                        service_name="yandexgpt"
                    )
                    
                    response.raise_for_status()
                    
                    return data["result"]["alternatives"][0]["message"]["text"]
                    
            except Exception as e:
                # Логируем ошибку
                await log_api_response(
                    request_id=request_id,
                    status_code=getattr(e, 'status', 0),
                    error=str(e),
                    service_name="yandexgpt"
                )
                raise