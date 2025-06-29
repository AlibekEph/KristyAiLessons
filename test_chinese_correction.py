#!/usr/bin/env python3
"""Тестирование YandexGPT коррекции китайских транскрипций"""

import asyncio
from src.services.enhanced_transcription_service import EnhancedTranscriptionService
from src.services.yandexgpt_service import YandexGPTService
from src.config import Settings


async def test_chinese_correction():
    """Тестирование коррекции китайских слов в транскрипции"""
    
    # Примеры транскрипций с ошибками (китайские слова записаны кириллицей)
    test_transcripts = [
        # Пример 1: Числа
        "Привет, Алибек. Сегодня мы с тобой будем разбирать новую тему на китайском. Числа. Один будет Е. Два будет О. Три будет САН. САН третий тон. Один, два, три. Пять будет У. Пять будет У, одиннадцать будет ШИЕ. Как дела? Будет НИХАУМА. Чтобы ответить Я хорошо, надо сказать ВОХЭНХАУ.",
        
        # Пример 2: Приветствия
        "На уроке мы изучили базовые фразы. Привет на китайском - это нихао. Как дела будет нихао ма. Меня зовут - во цзяо. До свидания - цзайцзянь.",
        
        # Пример 3: Смешанный текст
        "Сегодня повторяем числа от и до ши. Это один, ар, сан, сы, у, лю, ци, ба, цзю, ши. Преподаватель говорит: запомните, что ши это десять.",
    ]
    
    # Получаем настройки
    settings = Settings()
    
    try:
        # Создаем YandexGPT сервис
        yandex_service = YandexGPTService(
            folder_id=settings.YANDEX_FOLDER_ID,
            api_key=settings.YANDEX_API_KEY,
            model_uri=settings.YANDEX_MODEL_URI
        )
        
        print("🔧 YandexGPT сервис инициализирован")
        print("=" * 80)
        
        # Тестируем каждый пример
        for i, original_text in enumerate(test_transcripts, 1):
            print(f"\n📝 ТЕСТ {i}")
            print("-" * 60)
            print(f"Исходный текст:")
            print(f"🔤 {original_text}")
            
            try:
                # Применяем коррекцию
                corrected_text = await yandex_service._correct_chinese_transcript(original_text)
                
                print(f"\nИсправленный текст:")
                print(f"🌸 {corrected_text}")
                
                # Проверяем, добавились ли китайские символы
                has_chinese_original = any('\u4e00' <= char <= '\u9fff' for char in original_text)
                has_chinese_corrected = any('\u4e00' <= char <= '\u9fff' for char in corrected_text)
                
                if not has_chinese_original and has_chinese_corrected:
                    print("✅ Коррекция успешна: добавлены китайские иероглифы")
                elif has_chinese_original and has_chinese_corrected:
                    print("✅ Коррекция завершена: китайские символы сохранены/улучшены")
                else:
                    print("⚠️ Коррекция не добавила китайские символы")
                
            except Exception as e:
                print(f"❌ Ошибка коррекции: {e}")
            
            print("-" * 60)
        
        print("\n" + "=" * 80)
        
        # Тестируем Enhanced Transcription Service
        print("🚀 Тестирование Enhanced Transcription Service с коррекцией")
        print("-" * 60)
        
        enhanced_service = EnhancedTranscriptionService(
            recall_api_key=settings.RECALL_API_KEY,
            assemblyai_api_key=settings.ASSEMBLYAI_API_KEY
        )
        
        # Тестируем с фиктивным результатом
        test_result = {
            "text": test_transcripts[0],
            "confidence": 0.85,
            "language": "mixed"
        }
        
        corrected_result = await enhanced_service._apply_intelligent_post_processing(
            test_result, 
            "chinese"
        )
        
        print(f"Исходный текст: {test_result['text'][:100]}...")
        print(f"Результат после обработки: {corrected_result['text'][:100]}...")
        print(f"YandexGPT коррекция применена: {corrected_result.get('yandexgpt_correction_applied', False)}")
        
        if corrected_result.get('yandexgpt_correction_error'):
            print(f"❌ Ошибка: {corrected_result['yandexgpt_correction_error']}")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        print("💡 Убедитесь, что настройки YandexGPT указаны в .env файле:")
        print("   - YANDEX_FOLDER_ID")
        print("   - YANDEX_API_KEY")
        print("   - YANDEX_MODEL_URI (опционально)")


async def main():
    """Главная функция"""
    print("🧪 Тестирование YandexGPT коррекции китайских транскрипций")
    print("=" * 80)
    await test_chinese_correction()


if __name__ == "__main__":
    asyncio.run(main()) 