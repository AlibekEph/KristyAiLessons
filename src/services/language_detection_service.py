"""Universal language detection service without hardcoded word lists."""

import re
from typing import Dict, Any, List, Optional, Tuple
from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException
import logging

logger = logging.getLogger(__name__)


class LanguageDetectionService:
    """Service for automatic language detection and analysis"""
    
    # Unicode ranges for different scripts
    SCRIPT_RANGES = {
        'chinese': (0x4E00, 0x9FFF),  # CJK Unified Ideographs
        'cyrillic': (0x0400, 0x04FF),  # Cyrillic
        'latin': (0x0041, 0x007A),     # Basic Latin (A-Z, a-z)
    }
    
    # Supported lesson types
    LESSON_TYPES = {
        'chinese': ['ru', 'zh'],      # Russian + Chinese
        'english': ['ru', 'en']       # Russian + English
    }
    
    def __init__(self):
        self.min_text_length = 10  # Minimum text length for reliable detection
    
    def detect_language_mix(self, text: str) -> Dict[str, Any]:
        """Detect language composition in text"""
        
        if not text or len(text.strip()) < self.min_text_length:
            return self._empty_detection_result()
        
        # Clean text
        cleaned_text = self._clean_text(text)
        
        # Script-based analysis
        script_analysis = self._analyze_scripts(cleaned_text)
        
        # Library-based detection
        library_detection = self._library_detect(cleaned_text)
        
        # Combine results
        combined_result = self._combine_detections(script_analysis, library_detection)
        
        # Determine lesson type
        lesson_type = self._determine_lesson_type(combined_result)
        
        return {
            'script_analysis': script_analysis,
            'library_detection': library_detection,
            'combined_result': combined_result,
            'lesson_type': lesson_type,
            'confidence': combined_result.get('confidence', 0.0),
            'primary_language': combined_result.get('primary_language', 'unknown'),
            'detected_languages': combined_result.get('languages', []),
            'is_multilingual': len(combined_result.get('languages', [])) > 1
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean text for analysis"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove punctuation for better language detection
        text = re.sub(r'[^\w\s]', ' ', text)
        
        return text
    
    def _analyze_scripts(self, text: str) -> Dict[str, Any]:
        """Analyze text based on Unicode script ranges"""
        
        total_chars = len(text.replace(' ', ''))
        if total_chars == 0:
            return {'scripts': {}, 'dominant_script': 'unknown'}
        
        script_counts = {
            'chinese': 0,
            'cyrillic': 0, 
            'latin': 0,
            'other': 0
        }
        
        for char in text:
            if char.isspace():
                continue
                
            char_code = ord(char)
            classified = False
            
            for script, (start, end) in self.SCRIPT_RANGES.items():
                if start <= char_code <= end:
                    script_counts[script] += 1
                    classified = True
                    break
            
            if not classified:
                script_counts['other'] += 1
        
        # Calculate percentages
        script_percentages = {
            script: (count / total_chars) * 100 
            for script, count in script_counts.items()
        }
        
        # Find dominant script
        dominant_script = max(script_percentages.keys(), key=lambda k: script_percentages[k])
        
        return {
            'scripts': script_percentages,
            'dominant_script': dominant_script,
            'total_chars': total_chars
        }
    
    def _library_detect(self, text: str) -> Dict[str, Any]:
        """Use langdetect library for language detection"""
        
        try:
            # Single language detection
            primary_lang = detect(text)
            
            # Multiple language detection with probabilities
            lang_probs = detect_langs(text)
            
            languages = []
            for lang_prob in lang_probs:
                languages.append({
                    'language': lang_prob.lang,
                    'probability': float(lang_prob.prob)
                })
            
            return {
                'primary_language': primary_lang,
                'languages': languages,
                'success': True
            }
            
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}")
            return {
                'primary_language': 'unknown',
                'languages': [],
                'success': False,
                'error': str(e)
            }
    
    def _combine_detections(
        self, 
        script_analysis: Dict[str, Any], 
        library_detection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine script analysis and library detection"""
        
        languages = []
        confidence = 0.0
        primary_language = 'unknown'
        
        # Process library detection results
        if library_detection['success']:
            lib_languages = library_detection.get('languages', [])
            primary_language = library_detection.get('primary_language', 'unknown')
            
            # Get confidence from highest probability language
            if lib_languages:
                confidence = max(lang['probability'] for lang in lib_languages)
                languages = [lang['language'] for lang in lib_languages if lang['probability'] > 0.1]
        
        # Enhance with script analysis
        scripts = script_analysis.get('scripts', {})
        
        # Add languages based on script analysis
        if scripts.get('chinese', 0) > 5:  # >5% Chinese characters
            if 'zh' not in languages:
                languages.append('zh')
                
        if scripts.get('cyrillic', 0) > 5:  # >5% Cyrillic characters
            if 'ru' not in languages:
                languages.append('ru')
                
        if scripts.get('latin', 0) > 50 and not any(lang in languages for lang in ['zh', 'ru']):
            # Mostly Latin script and no other languages detected
            if 'en' not in languages:
                languages.append('en')
        
        # Adjust confidence based on script analysis
        dominant_script = script_analysis.get('dominant_script', 'unknown')
        if dominant_script != 'unknown' and dominant_script != 'other':
            confidence = min(confidence + 0.2, 1.0)  # Boost confidence
        
        return {
            'primary_language': primary_language,
            'languages': languages,
            'confidence': confidence,
            'script_dominant': dominant_script
        }
    
    def _determine_lesson_type(self, combined_result: Dict[str, Any]) -> str:
        """Determine lesson type based on detected languages"""
        
        detected_languages = set(combined_result.get('languages', []))
        
        # Check for Chinese lessons (Russian + Chinese)
        if 'ru' in detected_languages and 'zh' in detected_languages:
            return 'chinese'
        
        # Check for English lessons (Russian + English)
        if 'ru' in detected_languages and 'en' in detected_languages:
            return 'english'
        
        # Single language detection
        if 'zh' in detected_languages:
            return 'chinese'  # Assume Chinese lesson if Chinese detected
        
        if 'en' in detected_languages and 'ru' not in detected_languages:
            return 'english'  # English lesson if only English
        
        # Default based on primary language
        primary = combined_result.get('primary_language', 'unknown')
        if primary == 'zh':
            return 'chinese'
        elif primary == 'en':
            return 'english'
        
        return 'unknown'
    
    def _empty_detection_result(self) -> Dict[str, Any]:
        """Return empty detection result for invalid input"""
        return {
            'script_analysis': {'scripts': {}, 'dominant_script': 'unknown'},
            'library_detection': {'success': False, 'languages': []},
            'combined_result': {'languages': [], 'confidence': 0.0, 'primary_language': 'unknown'},
            'lesson_type': 'unknown',
            'confidence': 0.0,
            'primary_language': 'unknown',
            'detected_languages': [],
            'is_multilingual': False
        }
    
    def get_lesson_language_config(self, lesson_type: str) -> Dict[str, Any]:
        """Get language configuration for a lesson type"""
        
        if lesson_type not in self.LESSON_TYPES:
            lesson_type = 'chinese'  # Default
        
        expected_languages = self.LESSON_TYPES[lesson_type]
        
        return {
            'lesson_type': lesson_type,
            'expected_languages': expected_languages,
            'primary_language': expected_languages[0],  # First is primary (usually Russian)
            'secondary_language': expected_languages[1] if len(expected_languages) > 1 else None,
            'supports_multilingual': True
        }
    
    def calculate_quality_score(self, detection_result: Dict[str, Any], expected_lesson_type: str) -> float:
        """Calculate quality score for detection result"""
        
        detected_lesson_type = detection_result.get('lesson_type', 'unknown')
        confidence = detection_result.get('confidence', 0.0)
        is_multilingual = detection_result.get('is_multilingual', False)
        
        score = 0.0
        
        # Base score from confidence
        score += confidence * 0.4
        
        # Bonus for correct lesson type detection
        if detected_lesson_type == expected_lesson_type:
            score += 0.3
        
        # Bonus for multilingual detection in language lessons
        if is_multilingual and expected_lesson_type in ['chinese', 'english']:
            score += 0.2
        
        # Bonus for having expected languages
        expected_config = self.get_lesson_language_config(expected_lesson_type)
        expected_langs = set(expected_config['expected_languages'])
        detected_langs = set(detection_result.get('detected_languages', []))
        
        if expected_langs.intersection(detected_langs):
            score += 0.1
        
        return min(score, 1.0) 