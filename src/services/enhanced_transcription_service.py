"""Enhanced transcription service using automatic language detection without hardcoded words."""

import asyncio
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from .multilingual_transcription_service import MultilingualTranscriptionService
from .direct_assemblyai_service import DirectAssemblyAIService
from .language_detection_service import LanguageDetectionService
from .yandexgpt_service import YandexGPTService
from ..config import Settings

logger = logging.getLogger(__name__)


class EnhancedTranscriptionService:
    """Service combining multiple transcription approaches with automatic language detection"""
    
    def __init__(self, recall_api_key: str, assemblyai_api_key: str):
        self.recall_api_key = recall_api_key
        self.assemblyai_api_key = assemblyai_api_key
        
        # Initialize sub-services
        self.multilingual_service = MultilingualTranscriptionService(recall_api_key)
        self.direct_assemblyai = DirectAssemblyAIService(assemblyai_api_key)
        self.language_detector = LanguageDetectionService()
        
        # Initialize YandexGPT service for Chinese corrections
        settings = Settings()
        try:
            self.yandex_service = YandexGPTService(
                folder_id=settings.YANDEX_FOLDER_ID,
                api_key=settings.YANDEX_API_KEY,
                model_uri=settings.YANDEX_MODEL_URI
            )
        except Exception as e:
            logger.warning(f"YandexGPT service not available: {e}")
            self.yandex_service = None
    
    async def transcribe_lesson(
        self, 
        recording_id: str,
        lesson_type: str = "chinese",
        use_multiple_approaches: bool = True
    ) -> Dict[str, Any]:
        """Main transcription method using multiple approaches"""
        
        logger.info(f"Starting enhanced transcription for recording {recording_id}")
        
        if use_multiple_approaches:
            return await self._transcribe_with_multiple_approaches(recording_id, lesson_type)
        else:
            return await self._transcribe_single_approach(recording_id, lesson_type)
    
    async def _transcribe_with_multiple_approaches(
        self, 
        recording_id: str, 
        lesson_type: str
    ) -> Dict[str, Any]:
        """Use multiple approaches and combine results"""
        
        logger.info("Using multiple transcription approaches")
        
        # Approach 1: Recall API with multilingual settings
        recall_task = self._transcribe_via_recall(recording_id, lesson_type)
        
        # Approach 2: Direct AssemblyAI with audio URL
        direct_task = self._transcribe_via_direct_assemblyai(recording_id)
        
        # Run both approaches in parallel
        results = await asyncio.gather(recall_task, direct_task, return_exceptions=True)
        
        recall_result = results[0] if not isinstance(results[0], Exception) else None
        direct_result = results[1] if not isinstance(results[1], Exception) else None
        
        # Combine and enhance results
        combined_result = await self._combine_all_approaches(
            recall_result=recall_result,
            direct_result=direct_result,
            recording_id=recording_id,
            lesson_type=lesson_type
        )
        
        return combined_result
    
    async def _transcribe_via_recall(
        self, 
        recording_id: str, 
        lesson_type: str
    ) -> Optional[Dict[str, Any]]:
        """Transcribe using Recall API approach"""
        
        try:
            logger.info(f"Starting Recall API transcription for {recording_id}")
            
            # Create transcript via Recall
            transcript_response = await self.multilingual_service.create_multilingual_transcript(
                recording_id=recording_id,
                lesson_type=lesson_type
            )
            
            if not transcript_response:
                return None
            
            transcript_id = transcript_response.get("id")
            if not transcript_id:
                return None
            
            # Wait for completion and get with post-processing
            await asyncio.sleep(10)  # Initial wait
            
            result = await self.multilingual_service.get_transcript_with_post_processing(transcript_id)
            
            if result:
                result["transcription_method"] = "recall_api"
                result["transcript_id"] = transcript_id
                
            return result
            
        except Exception as e:
            logger.error(f"Error in Recall API transcription: {e}")
            return None
    
    async def _transcribe_via_direct_assemblyai(
        self, 
        recording_id: str
    ) -> Optional[Dict[str, Any]]:
        """Transcribe using direct AssemblyAI approach"""
        
        try:
            logger.info(f"Starting direct AssemblyAI transcription for {recording_id}")
            
            # First, get audio URL from Recall recording
            audio_url = await self._get_audio_url_from_recording(recording_id)
            if not audio_url:
                logger.warning("Could not get audio URL for direct AssemblyAI transcription")
                return None
            
            # Use multiple models approach
            result = await self.direct_assemblyai.transcribe_with_multiple_models(audio_url)
            
            if result:
                result["transcription_method"] = "direct_assemblyai"
                result["audio_url"] = audio_url
                
            return result
            
        except Exception as e:
            logger.error(f"Error in direct AssemblyAI transcription: {e}")
            return None
    
    async def _get_audio_url_from_recording(self, recording_id: str) -> Optional[str]:
        """Get audio URL from Recall recording"""
        
        import aiohttp
        
        headers = {
            "Authorization": f"Token {self.recall_api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"https://us-west-2.recall.ai/api/v1/recording/{recording_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Try to get video/audio URL
                        media_shortcuts = data.get("media_shortcuts", {})
                        video_mixed = media_shortcuts.get("video_mixed", {})
                        
                        if video_mixed and video_mixed.get("data", {}).get("download_url"):
                            return video_mixed["data"]["download_url"]
                        
                        return None
                    else:
                        logger.error(f"Failed to get recording data: {response.status}")
                        return None
                        
            except Exception as e:
                logger.error(f"Error getting audio URL: {e}")
                return None
    
    async def _combine_all_approaches(
        self,
        recall_result: Optional[Dict[str, Any]],
        direct_result: Optional[Dict[str, Any]],
        recording_id: str,
        lesson_type: str
    ) -> Dict[str, Any]:
        """Combine results from all approaches using automatic language detection"""
        
        logger.info("Combining results from all transcription approaches")
        
        # Analyze results with language detection
        approaches = {
            "recall_api": {
                "result": recall_result,
                "available": recall_result is not None,
                "text": self._extract_text_from_result(recall_result),
            },
            "direct_assemblyai": {
                "result": direct_result,
                "available": direct_result is not None,
                "text": direct_result.get("text", "") if direct_result else "",
            }
        }
        
        # Add language analysis for each approach
        for approach_name, approach_data in approaches.items():
            if approach_data["available"]:
                text = approach_data["text"]
                language_analysis = self.language_detector.detect_language_mix(text)
                approach_data["language_analysis"] = language_analysis
                approach_data["quality_score"] = self.language_detector.calculate_quality_score(
                    language_analysis, lesson_type
                )
        
        # Create unified timeline-based transcript
        unified_transcript = self._create_unified_timeline_transcript(approaches)
        
        # Select best approach based on quality scores
        best_approach = self._select_best_approach_by_quality(approaches, lesson_type)
        
        # Build combined result with unified transcript
        if approaches[best_approach]["result"]:
            combined_result = approaches[best_approach]["result"].copy()
        else:
            combined_result = {"text": "", "words": []}
        
        # Override with unified transcript
        combined_result.update(unified_transcript)
        
        # Add metadata about the combination process
        combined_result.update({
            "enhanced_transcription": True,
            "primary_method": best_approach,
            "unified_timeline": True,
            "approaches_analysis": {
                name: {
                    "available": data["available"],
                    "language_analysis": data.get("language_analysis", {}),
                    "quality_score": data.get("quality_score", 0.0)
                }
                for name, data in approaches.items()
            },
            "recording_id": recording_id,
            "lesson_type": lesson_type,
            "processing_timestamp": datetime.now().isoformat()
        })
        
        # Apply final language-aware post-processing
        combined_result = await self._apply_intelligent_post_processing(combined_result, lesson_type)
        
        # Add formatted output options
        combined_result["formatted_outputs"] = self._create_formatted_outputs(combined_result)
        
        return combined_result
    
    def _create_unified_timeline_transcript(self, approaches: Dict[str, Any]) -> Dict[str, Any]:
        """Create unified transcript based on timeline from all available approaches"""
        
        all_words = []
        
        # Extract words with timestamps from all approaches
        for approach_name, approach_data in approaches.items():
            if not approach_data["available"] or not approach_data["result"]:
                continue
            
            words = self._extract_words_with_timestamps(approach_data["result"], approach_name)
            all_words.extend(words)
        
        if not all_words:
            return {"text": "", "words": [], "unified_words": []}
        
        # Sort words by start time
        all_words.sort(key=lambda w: w.get("start", 0))
        
        # Create natural unified text using intelligent sentence reconstruction
        unified_text = self._create_natural_text_from_timeline(all_words)
        
        # Group words by speakers if available
        speaker_segments = self._group_words_by_speaker(all_words)
        
        return {
            "text": unified_text,
            "unified_words": all_words,
            "speaker_segments": speaker_segments,
            "total_words": len(all_words)
        }
    
    def _create_natural_text_from_timeline(self, words: List[Dict[str, Any]]) -> str:
        """Create natural flowing text from timeline words using confidence and context"""
        
        if not words:
            return ""
        
        # Filter words by confidence threshold
        high_confidence_words = []
        for word in words:
            confidence = word.get("confidence", 1.0)
            text = word.get("text", "").strip()
            
            # Include word if:
            # - High confidence (>= 0.3) OR
            # - It's punctuation OR
            # - It's a short common word
            if (confidence >= 0.3 or 
                len(text) <= 2 or 
                text in [".", ",", "!", "?", "的", "是", "了", "и", "в", "на", "с", "a", "the", "is", "to"]):
                high_confidence_words.append(word)
        
        if not high_confidence_words:
            # Fallback to all words if filtering removed too much
            high_confidence_words = words
        
        # Build natural sentences
        sentences = []
        current_sentence = []
        last_speaker = None
        
        import re
        
        for i, word in enumerate(high_confidence_words):
            text = word.get("text", "").strip()
            speaker = word.get("speaker", "Unknown")
            
            if not text:
                continue
            
            # Check if we should start a new sentence
            should_start_new_sentence = False
            
            # 1. Speaker change indicates new sentence
            if last_speaker and speaker != last_speaker:
                should_start_new_sentence = True
            
            # 2. Large time gap (>2 seconds) indicates pause/new thought
            if (i > 0 and 
                word.get("start", 0) - high_confidence_words[i-1].get("end", 0) > 2.0):
                should_start_new_sentence = True
            
            # 3. Sentence-ending punctuation
            if (current_sentence and 
                current_sentence[-1].get("text", "").endswith((".", "!", "?", "。", "！", "？"))):
                should_start_new_sentence = True
            
            # Start new sentence if needed
            if should_start_new_sentence and current_sentence:
                sentence_text = self._build_sentence_from_words(current_sentence)
                if sentence_text.strip():
                    sentences.append(sentence_text)
                current_sentence = []
            
            current_sentence.append(word)
            last_speaker = speaker
        
        # Add final sentence
        if current_sentence:
            sentence_text = self._build_sentence_from_words(current_sentence)
            if sentence_text.strip():
                sentences.append(sentence_text)
        
        # Join sentences naturally
        result = " ".join(sentences).strip()
        
        # Clean up the result
        result = self._clean_up_natural_text(result)
        
        return result
    
    def _build_sentence_from_words(self, words: List[Dict[str, Any]]) -> str:
        """Build a natural sentence from a list of words"""
        
        if not words:
            return ""
        
        text_parts = []
        
        for word in words:
            text = word.get("text", "").strip()
            if text:
                # Handle Chinese characters - no spaces needed
                if self._is_chinese_character(text):
                    text_parts.append(text)
                # Handle punctuation - attach to previous word
                elif text in [".", ",", "!", "?", ":", ";", "。", "，", "！", "？", "：", "；"]:
                    if text_parts:
                        text_parts[-1] += text
                    else:
                        text_parts.append(text)
                # Regular words - add with space
                else:
                    text_parts.append(text)
        
        # Join appropriately
        result_parts = []
        for i, part in enumerate(text_parts):
            if i == 0:
                result_parts.append(part)
            elif self._is_chinese_character(part) or self._is_chinese_character(text_parts[i-1]):
                # No space between Chinese characters
                result_parts.append(part)
            elif part.startswith((".", ",", "!", "?", ":", ";", "。", "，", "！", "？", "：", "；")):
                # No space before punctuation
                result_parts[-1] += part
            else:
                # Add space before regular words
                result_parts.append(" " + part)
        
        return "".join(result_parts)
    
    def _is_chinese_character(self, text: str) -> bool:
        """Check if text contains Chinese characters"""
        if not text:
            return False
        return any('\u4e00' <= char <= '\u9fff' for char in text)
    
    def _clean_up_natural_text(self, text: str) -> str:
        """Clean up the natural text to make it more readable"""
        
        import re
        
        # Fix multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Fix spaces around Chinese punctuation
        text = re.sub(r'\s+([。，！？：；])', r'\1', text)
        
        # Fix spaces before regular punctuation
        text = re.sub(r'\s+([.!?:;,])', r'\1', text)
        
        # Add space after punctuation if followed by letter
        text = re.sub(r'([.!?])([A-Za-zА-Яа-я])', r'\1 \2', text)
        text = re.sub(r'([。！？])([A-Za-zА-Яа-я])', r'\1 \2', text)
        
        # Capitalize first letter of sentences
        sentences = re.split(r'([.!?。！？]\s*)', text)
        capitalized_sentences = []
        
        for i, sentence in enumerate(sentences):
            if i % 2 == 0 and sentence.strip():  # Actual sentence content
                sentence = sentence.strip()
                if sentence and sentence[0].isalpha():
                    sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
            capitalized_sentences.append(sentence)
        
        result = ''.join(capitalized_sentences).strip()
        
        # Remove excessive punctuation
        result = re.sub(r'([.!?。！？]){2,}', r'\1', result)
        
        return result
    
    def _extract_words_with_timestamps(self, result: Dict[str, Any], source: str) -> List[Dict[str, Any]]:
        """Extract words with timestamps from different result formats"""
        
        words = []
        
        try:
            # For Recall API format (list of participants)
            if isinstance(result, list):
                for participant in result:
                    if "words" in participant:
                        for word in participant["words"]:
                            word_data = {
                                "text": word.get("text", ""),
                                "start": word.get("start", 0),
                                "end": word.get("end", 0),
                                "confidence": word.get("confidence", 1.0),
                                "speaker": word.get("speaker") or participant.get("speaker", "Unknown"),
                                "source": source,
                                "detected_language": word.get("detected_language", "unknown")
                            }
                            words.append(word_data)
            
            # For AssemblyAI format
            elif "words" in result:
                for word in result["words"]:
                    word_data = {
                        "text": word.get("text", ""),
                        "start": word.get("start", 0) / 1000.0 if word.get("start") else 0,  # Convert ms to seconds
                        "end": word.get("end", 0) / 1000.0 if word.get("end") else 0,
                        "confidence": word.get("confidence", 1.0),
                        "speaker": word.get("speaker", "Unknown"),
                        "source": source
                    }
                    words.append(word_data)
            
            # For simple text format - try to create words without timestamps
            elif "text" in result:
                text = result["text"]
                # Split into words and assign sequential timestamps (estimation)
                text_words = text.split()
                for i, word_text in enumerate(text_words):
                    word_data = {
                        "text": word_text,
                        "start": i * 0.5,  # Estimate 0.5 seconds per word
                        "end": (i + 1) * 0.5,
                        "confidence": 1.0,
                        "speaker": "Unknown",
                        "source": source,
                        "estimated_timing": True
                    }
                    words.append(word_data)
        
        except Exception as e:
            logger.warning(f"Error extracting words from {source}: {e}")
        
        return words
    
    def _group_words_by_speaker(self, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group consecutive words by speaker"""
        
        if not words:
            return []
        
        segments = []
        current_segment = None
        
        for word in words:
            speaker = word.get("speaker", "Unknown")
            
            # Start new segment if speaker changed or no current segment
            if current_segment is None or current_segment["speaker"] != speaker:
                if current_segment:
                    segments.append(current_segment)
                
                current_segment = {
                    "speaker": speaker,
                    "start": word.get("start", 0),
                    "end": word.get("end", 0),
                    "words": [word],
                    "text": word.get("text", "")
                }
            else:
                # Add word to current segment
                current_segment["words"].append(word)
                current_segment["text"] += " " + word.get("text", "")
                current_segment["end"] = word.get("end", current_segment["end"])
        
        # Add final segment
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    def _extract_text_from_result(self, result: Optional[Dict[str, Any]]) -> str:
        """Extract text from various result formats"""
        
        if not result:
            return ""
        
        # Try different text extraction methods
        if "text" in result:
            return result["text"]
        
        # For Recall API format (list of participants)
        if isinstance(result, list) and result:
            texts = []
            for participant in result:
                if "words" in participant:
                    words = [word.get("text", "") for word in participant["words"]]
                    texts.append(" ".join(words))
            return " ".join(texts)
        
        return ""
    
    def _select_best_approach_by_quality(
        self, 
        approaches: Dict[str, Any], 
        lesson_type: str
    ) -> str:
        """Select the best transcription approach based on quality scores"""
        
        scores = {}
        
        for approach_name, approach_data in approaches.items():
            if not approach_data["available"]:
                scores[approach_name] = 0
                continue
            
            # Base score from language detection quality
            quality_score = approach_data.get("quality_score", 0.0)
            score = quality_score * 100
            
            # Add text length bonus (longer transcripts are generally better)
            text_length = len(approach_data["text"])
            score += min(text_length / 10, 50)  # Cap at 50 bonus points
            
            # Special handling for multilingual lessons (chinese, english, etc.)
            if lesson_type in ["chinese", "english", "spanish"]:
                # For multilingual lessons, prefer multilingual approach
                if approach_name == "multilingual":
                    score += 50  # Strong bonus for multilingual
                    # Additional bonus if it shows mixed languages
                    lang_analysis = approach_data.get("language_analysis", {})
                    if lang_analysis.get("is_multilingual", False):
                        score += 30
                elif approach_name.startswith("specific_"):
                    # Penalty for language-specific approaches in multilingual contexts
                    # unless they're exceptionally good
                    if quality_score < 0.8:
                        score -= 20
            
            # Approach-specific bonuses for non-multilingual cases
            else:
                if approach_name == "recall_api":
                    # Recall API is good for speaker identification
                    score += 10
                elif approach_name == "direct_assemblyai":
                    # Direct AssemblyAI might have better accuracy
                    score += 15
            
            # Penalty for very short results
            if text_length < 20:
                score *= 0.5
            
            scores[approach_name] = score
        
        if not scores or all(score == 0 for score in scores.values()):
            # Default fallback order: multilingual -> recall_api -> direct_assemblyai
            for fallback in ["multilingual", "recall_api", "direct_assemblyai"]:
                if fallback in approaches and approaches[fallback]["available"]:
                    return fallback
            # Last resort - return any available approach
            return next((name for name, data in approaches.items() if data["available"]), "recall_api")
        
        best_approach = max(scores.keys(), key=lambda k: scores[k])
        logger.info(f"Approach quality scores: {scores}, selected: {best_approach}")
        
        return best_approach
    
    async def _apply_intelligent_post_processing(
        self, 
        result: Dict[str, Any], 
        lesson_type: str
    ) -> Dict[str, Any]:
        """Apply intelligent post-processing based on language detection"""
        
        text = result.get("text", "")
        
        # Perform language analysis on the final text
        language_analysis = self.language_detector.detect_language_mix(text)
        
        # Get lesson configuration
        lesson_config = self.language_detector.get_lesson_language_config(lesson_type)
        
        # Apply algorithmic improvements
        improved_text = self._apply_algorithmic_improvements(text, language_analysis, lesson_config)
        
        # Apply YandexGPT corrections for Chinese lessons
        if lesson_type == "chinese" and self.yandex_service and improved_text:
            try:
                logger.info("Applying YandexGPT Chinese correction to transcript")
                corrected_text = await self.yandex_service._correct_chinese_transcript(improved_text)
                
                # Verify the correction improved the text
                if corrected_text and len(corrected_text.strip()) > 0:
                    # Additional verification - corrected text should contain Chinese characters for Chinese lessons
                    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in corrected_text)
                    if has_chinese or lesson_type != "chinese":
                        improved_text = corrected_text
                        result["yandexgpt_correction_applied"] = True
                        logger.info("YandexGPT correction successfully applied")
                    else:
                        logger.warning("YandexGPT correction did not add Chinese characters, keeping original")
                        result["yandexgpt_correction_applied"] = False
                else:
                    logger.warning("YandexGPT correction returned empty result, keeping original")
                    result["yandexgpt_correction_applied"] = False
                    
            except Exception as e:
                logger.error(f"YandexGPT correction failed: {e}")
                result["yandexgpt_correction_error"] = str(e)
                result["yandexgpt_correction_applied"] = False
        
        # Update result
        result["text"] = improved_text
        result["language_analysis"] = language_analysis
        result["lesson_config"] = lesson_config
        result["post_processing_applied"] = True
        
        # Add quality metrics
        result["quality_metrics"] = self._calculate_automatic_quality_metrics(
            improved_text, language_analysis, lesson_config
        )
        
        return result
    
    def _apply_algorithmic_improvements(
        self, 
        text: str, 
        language_analysis: Dict[str, Any], 
        lesson_config: Dict[str, Any]
    ) -> str:
        """Apply algorithmic text improvements without hardcoded replacements"""
        
        # Only apply basic cleaning and formatting improvements
        improved_text = text
        
        # 1. Fix multiple spaces
        import re
        improved_text = re.sub(r'\s+', ' ', improved_text)
        
        # 2. Fix sentence boundaries
        improved_text = re.sub(r'([.!?])\s*([a-zA-Zа-яё])', r'\1 \2', improved_text)
        
        # 3. Capitalize first letter of sentences
        sentences = improved_text.split('. ')
        capitalized_sentences = []
        for sentence in sentences:
            if sentence:
                sentence = sentence.strip()
                if sentence:
                    sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                capitalized_sentences.append(sentence)
        
        if capitalized_sentences:
            improved_text = '. '.join(capitalized_sentences)
        
        # 4. Remove excessive punctuation
        improved_text = re.sub(r'([.!?]){2,}', r'\1', improved_text)
        
        return improved_text.strip()
    
    def _calculate_automatic_quality_metrics(
        self, 
        text: str, 
        language_analysis: Dict[str, Any], 
        lesson_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate quality metrics using automatic analysis"""
        
        metrics = {
            "text_length": len(text),
            "word_count": len(text.split()),
            "character_count": len(text),
            "language_confidence": language_analysis.get("confidence", 0.0),
            "detected_languages": language_analysis.get("detected_languages", []),
            "is_multilingual": language_analysis.get("is_multilingual", False),
            "lesson_type_match": language_analysis.get("lesson_type", "unknown") == lesson_config.get("lesson_type", "unknown")
        }
        
        # Calculate overall quality score
        quality_factors = []
        
        # Text length factor
        if metrics["word_count"] > 10:
            quality_factors.append(min(metrics["word_count"] / 50, 1.0))
        else:
            quality_factors.append(0.2)
        
        # Language confidence factor
        quality_factors.append(metrics["language_confidence"])
        
        # Multilingual bonus for language lessons
        if metrics["is_multilingual"] and lesson_config.get("lesson_type") in ["chinese", "english"]:
            quality_factors.append(0.8)
        else:
            quality_factors.append(0.5)
        
        # Lesson type match bonus
        if metrics["lesson_type_match"]:
            quality_factors.append(0.9)
        else:
            quality_factors.append(0.6)
        
        metrics["overall_quality"] = sum(quality_factors) / len(quality_factors)
        
        return metrics
    
    async def _transcribe_single_approach(
        self, 
        recording_id: str, 
        lesson_type: str
    ) -> Dict[str, Any]:
        """Use single best approach for faster processing"""
        
        # Use Recall API as default single approach
        result = await self._transcribe_via_recall(recording_id, lesson_type)
        
        if result:
            result["enhanced_transcription"] = False
            result["single_approach_used"] = True
            
            # Still apply intelligent post-processing
            text = self._extract_text_from_result(result)
            if text:
                result["text"] = text
                result = await self._apply_intelligent_post_processing(result, lesson_type)
                
            return result
        
        return {"text": "", "words": [], "error": "Transcription failed"}
    
    def _create_formatted_outputs(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create different formatted versions of the transcript"""
        
        outputs = {}
        
        # 1. Simple unified text (what user requested)
        outputs["unified_text"] = result.get("text", "")
        
        # 2. Speaker-separated format
        if "speaker_segments" in result:
            speaker_text_lines = []
            for segment in result["speaker_segments"]:
                speaker = segment.get("speaker", "Unknown")
                text = segment.get("text", "")
                speaker_text_lines.append(f"{speaker}: {text}")
            outputs["speaker_separated"] = "\n".join(speaker_text_lines)
        
        # 3. Timeline format with timestamps
        if "unified_words" in result:
            timeline_lines = []
            for word in result["unified_words"][:20]:  # First 20 words as example
                start = word.get("start", 0)
                end = word.get("end", 0)
                text = word.get("text", "")
                speaker = word.get("speaker", "Unknown")
                timeline_lines.append(f"[{start:.1f}-{end:.1f}s] {speaker}: {text}")
            outputs["timeline_format"] = "\n".join(timeline_lines)
        
        # 4. Language-aware format (for multilingual content)
        if "unified_words" in result:
            language_lines = []
            current_language = None
            current_line = ""
            
            for word in result["unified_words"]:
                word_language = word.get("detected_language", "unknown")
                text = word.get("text", "")
                
                if word_language != current_language:
                    if current_line:
                        language_lines.append(f"[{current_language}] {current_line}")
                    current_language = word_language
                    current_line = text
                else:
                    current_line += " " + text
            
            if current_line:
                language_lines.append(f"[{current_language}] {current_line}")
            
            outputs["language_separated"] = "\n".join(language_lines)
        
        return outputs
    
    async def _apply_dual_language_processing(
        self, 
        result: Dict[str, Any], 
        lesson_type: str
    ) -> Dict[str, Any]:
        """Apply dual-language processing using separate Russian and Chinese transcripts"""
        
        text = result.get("text", "")
        
        # Perform language analysis on the final text
        language_analysis = self.language_detector.detect_language_mix(text)
        
        # Get lesson configuration
        lesson_config = self.language_detector.get_lesson_language_config(lesson_type)
        
        # Apply algorithmic improvements first
        improved_text = self._apply_algorithmic_improvements(text, language_analysis, lesson_config)
        
        # Apply dual-language processing for Chinese lessons
        if lesson_type == "chinese" and self.yandex_service and improved_text:
            try:
                logger.info("Starting dual-language transcript processing")
                
                # Process with dual-language approach
                dual_result = await self.yandex_service.process_transcript_with_dual_approach(improved_text)
                
                # Update result with dual-language processing data
                result["dual_language_processing"] = {
                    "original_transcript": dual_result["original_transcript"],
                    "russian_transcript": dual_result["russian_transcript"],
                    "chinese_transcript": dual_result["chinese_transcript"],
                    "analysis": dual_result["analysis"],
                    "optimal_transcript": dual_result["optimal_transcript"],
                    "processing_method": dual_result["processing_method"]
                }
                
                # Use optimal transcript as main text
                improved_text = dual_result["optimal_transcript"]
                result["text"] = improved_text
                result["dual_language_applied"] = True
                
                logger.info("Dual-language processing successfully applied")
                
                # Verify the processing improved the text
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in improved_text)
                result["dual_language_quality"] = {
                    "has_chinese_characters": has_chinese,
                    "text_length": len(improved_text),
                    "processing_successful": True
                }
                
            except Exception as e:
                logger.error(f"Dual-language processing failed: {e}")
                result["dual_language_error"] = str(e)
                result["dual_language_applied"] = False
        
        # Update other result fields
        result["language_analysis"] = language_analysis
        result["lesson_config"] = lesson_config
        result["dual_language_post_processing_applied"] = True
        
        # Add quality metrics
        result["quality_metrics"] = self._calculate_automatic_quality_metrics(
            improved_text, language_analysis, lesson_config
        )
        
        return result

    async def transcribe_lesson_with_comparison(
        self, 
        recording_id: str,
        lesson_type: str = "chinese",
        use_multiple_approaches: bool = True
    ) -> Dict[str, Any]:
        """Enhanced transcription with comparison between standard and dual-language approaches"""
        
        logger.info(f"Starting comparative transcription analysis for recording {recording_id}")
        
        # Get base transcription result
        if use_multiple_approaches:
            base_result = await self._transcribe_with_multiple_approaches(recording_id, lesson_type)
        else:
            base_result = await self._transcribe_single_approach(recording_id, lesson_type)
        
        # Create two versions for comparison
        standard_result = base_result.copy()
        dual_language_result = base_result.copy()
        
        # Apply standard processing
        standard_result = await self._apply_intelligent_post_processing(standard_result, lesson_type)
        
        # Apply dual-language processing
        dual_language_result = await self._apply_dual_language_processing(dual_language_result, lesson_type)
        
        # Create comparative analysis
        comparison_analysis = await self._compare_processing_approaches(
            standard_result, 
            dual_language_result, 
            lesson_type
        )
        
        # Build comprehensive result
        comparative_result = {
            "recording_id": recording_id,
            "lesson_type": lesson_type,
            "comparison_analysis": comparison_analysis,
            "approaches": {
                "standard": {
                    "method": "standard_correction",
                    "text": standard_result.get("text", ""),
                    "applied": standard_result.get("yandexgpt_correction_applied", False),
                    "quality_metrics": standard_result.get("quality_metrics", {}),
                    "processing_timestamp": datetime.now().isoformat()
                },
                "dual_language": {
                    "method": "dual_language_processing",
                    "text": dual_language_result.get("text", ""),
                    "applied": dual_language_result.get("dual_language_applied", False),
                    "quality_metrics": dual_language_result.get("quality_metrics", {}),
                    "detailed_processing": dual_language_result.get("dual_language_processing", {}),
                    "processing_timestamp": datetime.now().isoformat()
                }
            },
            "recommended_approach": comparison_analysis.get("recommended_approach", "standard"),
            "enhanced_transcription": True,
            "comparative_analysis_completed": True
        }
        
        # Add the better result as main text
        if comparison_analysis.get("recommended_approach") == "dual_language":
            comparative_result["text"] = dual_language_result.get("text", "")
            comparative_result["primary_method"] = "dual_language"
        else:
            comparative_result["text"] = standard_result.get("text", "")
            comparative_result["primary_method"] = "standard"
        
        return comparative_result
    
    async def _compare_processing_approaches(
        self, 
        standard_result: Dict[str, Any], 
        dual_language_result: Dict[str, Any],
        lesson_type: str
    ) -> Dict[str, Any]:
        """Compare standard and dual-language processing approaches"""
        
        standard_text = standard_result.get("text", "")
        dual_language_text = dual_language_result.get("text", "")
        
        # Basic metrics comparison
        standard_metrics = {
            "text_length": len(standard_text),
            "has_chinese": any('\u4e00' <= char <= '\u9fff' for char in standard_text),
            "applied_successfully": standard_result.get("yandexgpt_correction_applied", False),
            "processing_time": "fast"
        }
        
        dual_language_metrics = {
            "text_length": len(dual_language_text),
            "has_chinese": any('\u4e00' <= char <= '\u9fff' for char in dual_language_text),
            "applied_successfully": dual_language_result.get("dual_language_applied", False),
            "processing_time": "slower",
            "has_detailed_analysis": bool(dual_language_result.get("dual_language_processing", {}))
        }
        
        # Determine recommendation
        recommended_approach = "standard"  # Default
        
        if dual_language_metrics["applied_successfully"]:
            if dual_language_metrics["has_chinese"] and dual_language_metrics["text_length"] > standard_metrics["text_length"] * 0.8:
                recommended_approach = "dual_language"
        
        comparison_summary = {
            "standard_metrics": standard_metrics,
            "dual_language_metrics": dual_language_metrics,
            "recommended_approach": recommended_approach,
            "comparison_reasons": [
                f"Standard approach: {'✓' if standard_metrics['applied_successfully'] else '✗'} Applied successfully",
                f"Dual-language approach: {'✓' if dual_language_metrics['applied_successfully'] else '✗'} Applied successfully", 
                f"Chinese characters: Standard {'✓' if standard_metrics['has_chinese'] else '✗'}, Dual-language {'✓' if dual_language_metrics['has_chinese'] else '✗'}",
                f"Text quality: Standard {standard_metrics['text_length']} chars, Dual-language {dual_language_metrics['text_length']} chars"
            ],
            "analysis_completed": True
        }
        
        # Add YandexGPT-based comparison if dual-language has analysis
        if dual_language_result.get("dual_language_processing", {}).get("analysis"):
            comparison_summary["yandex_analysis"] = dual_language_result["dual_language_processing"]["analysis"]
        
        return comparison_summary 