"""Direct AssemblyAI service using automatic language detection."""

import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from .language_detection_service import LanguageDetectionService

logger = logging.getLogger(__name__)


class DirectAssemblyAIService:
    """Service for direct interaction with AssemblyAI API using automatic language detection"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.assemblyai.com/v2"
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
        self.language_detector = LanguageDetectionService()
    
    async def transcribe_audio_url(
        self, 
        audio_url: str, 
        lesson_type: str = "chinese",
        language_code: Optional[str] = None,
        enable_multilingual: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Transcribe audio from URL with automatic language optimization"""
        
        # Get lesson configuration
        lesson_config = self.language_detector.get_lesson_language_config(lesson_type)
        
        # Build transcription config
        config = self._build_optimized_transcription_config(
            lesson_config, language_code, enable_multilingual
        )
        config["audio_url"] = audio_url
        
        logger.info(f"Starting AssemblyAI transcription for {lesson_type} lesson")
        
        # Submit transcription job
        transcript_id = await self._submit_transcription(config)
        if not transcript_id:
            return None
        
        # Poll for completion
        result = await self._poll_transcription(transcript_id)
        
        # Apply post-processing if result exists
        if result:
            result = self._apply_intelligent_post_processing(result, lesson_config)
        
        return result
    
    def _build_optimized_transcription_config(
        self, 
        lesson_config: Dict[str, Any],
        language_code: Optional[str] = None,
        enable_multilingual: bool = True
    ) -> Dict[str, Any]:
        """Build optimized transcription configuration based on lesson type"""
        
        config = {
            # Core settings - use best available
            "speech_model": "best",
            "punctuate": True,
            "format_text": True,
            "dual_channel": False,
            
            # Speaker identification
            "speaker_labels": True,
            
            # Language settings based on lesson configuration
            "language_detection": enable_multilingual,
        }
        
        # Configure language settings based on lesson type
        expected_languages = lesson_config.get('expected_languages', [])
        
        if language_code and not enable_multilingual:
            # Specific language requested
            config["language_code"] = language_code
            config["language_detection"] = False
        elif len(expected_languages) == 1 and not enable_multilingual:
            # Single language lesson
            config["language_code"] = expected_languages[0]
            config["language_detection"] = False
        else:
            # Multi-language lesson - use automatic detection
            config["language_detection"] = True
            # Remove language_code to let AssemblyAI auto-detect
            config.pop("language_code", None)
        
        logger.info(f"Built transcription config for lesson type {lesson_config.get('lesson_type', 'unknown')}")
        return config
    
    async def _submit_transcription(self, config: Dict[str, Any]) -> Optional[str]:
        """Submit transcription job to AssemblyAI"""
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/transcript",
                    json=config,
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        transcript_id = data.get("id")
                        logger.info(f"Submitted transcription job: {transcript_id}")
                        return transcript_id
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to submit transcription: {response.status} - {error_text}")
                        return None
                        
            except Exception as e:
                logger.error(f"Error submitting transcription: {e}")
                return None
    
    async def _poll_transcription(
        self, 
        transcript_id: str, 
        max_wait_time: int = 300,
        poll_interval: int = 5
    ) -> Optional[Dict[str, Any]]:
        """Poll transcription until completion"""
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < max_wait_time:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        f"{self.base_url}/transcript/{transcript_id}",
                        headers=self.headers
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            status = data.get("status")
                            
                            if status == "completed":
                                logger.info(f"Transcription {transcript_id} completed successfully")
                                return data
                            elif status == "error":
                                error_msg = data.get("error", "Unknown error")
                                logger.error(f"Transcription {transcript_id} failed: {error_msg}")
                                return None
                            elif status in ["queued", "processing"]:
                                logger.info(f"Transcription {transcript_id} status: {status}")
                                await asyncio.sleep(poll_interval)
                                continue
                            
                except Exception as e:
                    logger.error(f"Error polling transcription {transcript_id}: {e}")
                    await asyncio.sleep(poll_interval)
        
        logger.warning(f"Transcription {transcript_id} timed out after {max_wait_time} seconds")
        return None
    
    async def transcribe_with_multiple_models(
        self, 
        audio_url: str,
        lesson_type: str = "chinese"
    ) -> Dict[str, Any]:
        """Use multiple approaches and select best result automatically"""
        
        logger.info(f"Starting multi-model transcription for {lesson_type} lesson")
        
        # Get lesson configuration
        lesson_config = self.language_detector.get_lesson_language_config(lesson_type)
        expected_languages = lesson_config.get('expected_languages', ['ru', 'zh'])
        
        # Create tasks for different approaches
        tasks = []
        task_names = []
        
        # Always include multilingual approach
        tasks.append(self.transcribe_audio_url(
            audio_url, lesson_type=lesson_type, enable_multilingual=True
        ))
        task_names.append("multilingual")
        
        # Add language-specific approaches for expected languages
        for lang_code in expected_languages:
            tasks.append(self.transcribe_audio_url(
                audio_url, lesson_type=lesson_type, 
                language_code=lang_code, enable_multilingual=False
            ))
            task_names.append(f"specific_{lang_code}")
        
        # Run all transcriptions in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = {}
        for i, result in enumerate(results):
            if not isinstance(result, Exception) and result:
                processed_results[task_names[i]] = result
        
        # Combine and analyze results using automatic quality assessment
        combined_result = self._combine_transcription_results_intelligently(
            processed_results, lesson_config
        )
        
        return combined_result
    
    def _combine_transcription_results_intelligently(
        self, 
        results: Dict[str, Dict[str, Any]],
        lesson_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Intelligently combine results using automatic quality assessment"""
        
        if not results:
            return {"text": "", "words": [], "error": "No successful transcriptions"}
        
        # Analyze each result with language detection
        results_analysis = {}
        
        for approach_name, result in results.items():
            text = result.get("text", "")
            
            # Perform language analysis
            language_analysis = self.language_detector.detect_language_mix(text)
            
            # Calculate quality score
            quality_score = self.language_detector.calculate_quality_score(
                language_analysis, lesson_config.get('lesson_type', 'chinese')
            )
            
            results_analysis[approach_name] = {
                "result": result,
                "text": text,
                "language_analysis": language_analysis,
                "quality_score": quality_score,
                "confidence": result.get("confidence", 0.0),
                "text_length": len(text)
            }
        
        # Select best approach based on comprehensive scoring
        best_approach = self._select_best_approach_by_comprehensive_score(
            results_analysis, lesson_config
        )
        
        if best_approach and results_analysis[best_approach]["result"]:
            enhanced_result = results_analysis[best_approach]["result"].copy()
            enhanced_result.update({
                "model_comparison": results_analysis,
                "selected_model": best_approach,
                "selection_method": "comprehensive_quality_score",
                "final_language_analysis": results_analysis[best_approach]["language_analysis"]
            })
            return enhanced_result
        
        # Fallback to first available result
        first_result = next(iter(results.values()))
        first_result["model_comparison"] = results_analysis
        first_result["selected_model"] = "fallback"
        return first_result
    
    def _select_best_approach_by_comprehensive_score(
        self, 
        results_analysis: Dict[str, Any],
        lesson_config: Dict[str, Any]
    ) -> Optional[str]:
        """Select best approach using comprehensive automatic scoring"""
        
        scores = {}
        lesson_type = lesson_config.get('lesson_type', 'unknown')
        
        # Special handling for Chinese lessons - prioritize results with Russian content
        if lesson_type == "chinese":
            for approach_name, analysis in results_analysis.items():
                text = analysis.get("text", "")
                
                # Check if text contains Cyrillic characters (Russian)
                contains_russian = any('\u0400' <= char <= '\u04FF' for char in text)
                
                if contains_russian:
                    # Give massive bonus to approaches with Russian text for Chinese lessons
                    scores[approach_name] = 1000  # Overwhelming priority
                    logger.info(f"Chinese lesson: {approach_name} contains Russian text, giving maximum priority")
                else:
                    # Standard scoring for non-Russian text
                    scores[approach_name] = 10
                    logger.info(f"Chinese lesson: {approach_name} contains no Russian text, low priority")
        else:
            # Standard scoring for non-Chinese lessons
            for approach_name, analysis in results_analysis.items():
                score = 0.0
                
                # Base score from language detection quality (40% weight)
                quality_score = analysis.get("quality_score", 0.0)
                score += quality_score * 40
                
                # AssemblyAI confidence score (30% weight)
                confidence = analysis.get("confidence", 0.0)
                score += confidence * 30
                
                # Text length bonus (20% weight) - longer transcripts often better
                text_length = analysis.get("text_length", 0)
                length_score = min(text_length / 100, 1.0)  # Normalize to 0-1
                score += length_score * 20
                
                # Special handling for multilingual lessons (10% weight base)
                language_analysis = analysis.get("language_analysis", {})
                is_multilingual = language_analysis.get("is_multilingual", False)
                
                if lesson_type in ["english", "spanish"]:
                    # For multilingual lessons, strongly prefer multilingual approach
                    if approach_name == "multilingual" and is_multilingual:
                        score += 25  # Strong bonus for multilingual detection
                    elif approach_name.startswith("specific_") and not is_multilingual:
                        # Penalty for language-specific when lesson should be multilingual
                        score -= 15
                    elif approach_name == "multilingual":
                        score += 10  # Still prefer multilingual even if not detected as such
                else:
                    # For non-multilingual lessons, standard bonus
                    if is_multilingual:
                        score += 10
                
                # Penalty for very short results
                if text_length < 10:
                    score *= 0.5
                
                scores[approach_name] = score
        
        if not scores:
            return None
        
        best_approach = max(scores.keys(), key=lambda k: scores[k])
        logger.info(f"Comprehensive approach scores for {lesson_type}: {scores}, selected: {best_approach}")
        return best_approach
    
    def _apply_intelligent_post_processing(
        self, 
        result: Dict[str, Any], 
        lesson_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply intelligent post-processing based on automatic analysis"""
        
        text = result.get("text", "")
        
        if not text:
            return result
        
        # Perform language analysis
        language_analysis = self.language_detector.detect_language_mix(text)
        
        # Apply algorithmic text improvements
        improved_text = self._apply_text_improvements(text, language_analysis)
        
        # Update result
        result["text"] = improved_text
        result["language_analysis"] = language_analysis
        result["lesson_config"] = lesson_config
        result["post_processing_applied"] = True
        
        # Calculate quality metrics
        result["quality_metrics"] = {
            "original_length": len(text),
            "improved_length": len(improved_text),
            "language_confidence": language_analysis.get("confidence", 0.0),
            "detected_languages": language_analysis.get("detected_languages", []),
            "is_multilingual": language_analysis.get("is_multilingual", False),
            "lesson_type_match": language_analysis.get("lesson_type", "unknown") == lesson_config.get("lesson_type", "unknown")
        }
        
        return result
    
    def _apply_text_improvements(
        self, 
        text: str, 
        language_analysis: Dict[str, Any]
    ) -> str:
        """Apply algorithmic text improvements without hardcoded replacements"""
        
        import re
        
        improved_text = text
        
        # 1. Fix spacing issues
        improved_text = re.sub(r'\s+', ' ', improved_text)
        
        # 2. Fix sentence boundaries
        improved_text = re.sub(r'([.!?])\s*([a-zA-Zа-яё\u4e00-\u9fff])', r'\1 \2', improved_text)
        
        # 3. Capitalize sentence starts
        sentences = re.split(r'([.!?]\s+)', improved_text)
        capitalized_sentences = []
        
        for i, sentence in enumerate(sentences):
            if i % 2 == 0 and sentence.strip():  # Actual sentence content
                sentence = sentence.strip()
                if sentence:
                    # Capitalize first character if it's a letter
                    if sentence[0].isalpha():
                        sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
            capitalized_sentences.append(sentence)
        
        improved_text = ''.join(capitalized_sentences)
        
        # 4. Remove excessive punctuation
        improved_text = re.sub(r'([.!?]){2,}', r'\1', improved_text)
        
        # 5. Clean up extra whitespace at start/end
        improved_text = improved_text.strip()
        
        return improved_text 