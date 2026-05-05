"""
KSL Translation using mT5
Translates between KSL gloss, English, and Kiswahili
"""
import re
from typing import List, Tuple

class KSLTranslator:
    """
    Rule-based KSL translator (placeholder for mT5 model).
    
    Full implementation would use Hugging Face transformers:
    from transformers import MT5ForConditionalGeneration, T5Tokenizer
    """
    
    # Example translations for demonstration
    TRANSLATIONS = {
        ('ksl', 'eng'): {
            'HELLO YOU HOW?': 'Hello, how are you?',
            'FUTURE LEARN SIGN I WILL': 'I will learn sign language in the future',
            'YESTERDAY MARKET I GO': 'I went to the market yesterday',
            'THANK YOU VERY MUCH': 'Thank you very much',
            'PLEASE HELP ME': 'Please help me',
            'I AM DEAF': 'I am deaf',
            'I AM HARD OF HEARING': 'I am hard of hearing',
            'GOOD MORNING': 'Good morning',
            'GOOD AFTERNOON': 'Good afternoon',
            'GOOD NIGHT': 'Good night',
            'MOTHER FATHER SIBLING': 'Mother, father, sibling',
            'TEACHER STUDENT CLASS': 'Teacher, student, class',
            'SCHOOL I GO WILL': 'I will go to school',
            'WATER DRINK I WANT': 'I want to drink water',
            'FOOD EAT I': 'I eat food',
            'HAPPY I AM': 'I am happy',
            'SAD I AM': 'I am sad',
            'TIRED I AM': 'I am tired',
            'SCARED I AM': 'I am scared',
            'WHERE BATHROOM?': 'Where is the bathroom?',
            'WHAT TIME?': 'What time is it?',
        },
        ('eng', 'ksl'): {
            'Hello, how are you?': 'HELLO YOU HOW?',
            'I will learn sign language': 'FUTURE LEARN SIGN I WILL',
            'I went to the market yesterday': 'YESTERDAY MARKET I GO',
            'Thank you very much': 'THANK YOU VERY MUCH',
            'Please help me': 'PLEASE HELP ME',
            'I am deaf': 'I AM DEAF',
            'I am hard of hearing': 'I AM HARD OF HEARING',
            'Good morning': 'GOOD MORNING',
            'Good afternoon': 'GOOD AFTERNOON',
            'Good night': 'GOOD NIGHT',
            'Where is the bathroom?': 'WHERE BATHROOM?',
        },
        ('eng', 'swa'): {
            'Hello, how are you?': 'Habari, uko mzima?',
            'Thank you': 'Asante',
            'Please': 'Tafadhali',
            'Good morning': 'Habari za asubuhi',
            'Good afternoon': 'Habari za mchana',
            'Good night': 'Usiku mwema',
            'I am deaf': 'Mimi ni kiziwi',
            'I am hard of hearing': 'Mimi ninawasikia kwa shida',
            'Where is the bathroom?': 'Choo kiko wapi?',
        },
        ('swa', 'eng'): {
            'Habari': 'Hello',
            'Asante': 'Thank you',
            'Tafadhali': 'Please',
            'Habari za asubuhi': 'Good morning',
            'Habari za mchana': 'Good afternoon',
            'Usiku mwema': 'Good night',
            'Mimi ni kiziwi': 'I am deaf',
            'Choo kiko wapi?': 'Where is the bathroom?',
        }
    }
    
    def __init__(self):
        """Initialize translator."""
        self.regional_variations = {
            'nairobi': {},  # Standard KSL
            'mombasa': {
                'slow_pace': True,
                'handshape_variations': {}
            },
            'kisumu': {
                'luo_influenced': True
            },
            'rural': {
                'simplified': True
            }
        }
    
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        region: str = 'nairobi'
    ) -> Tuple[str, float]:
        """
        Translate text between languages.
        
        Args:
            text: Input text
            source_lang: Source language code (ksl, eng, swa)
            target_lang: Target language code (ksl, eng, swa)
            region: Regional variation (nairobi, mombasa, kisumu, rural)
            
        Returns:
            translated_text: Translated text
            confidence: Confidence score 0-1
        """
        key = (source_lang, target_lang)
        
        # Direct lookup
        if key in self.TRANSLATIONS:
            translations = self.TRANSLATIONS[key]
            if text.upper() in translations:
                return translations[text.upper()], 0.95
            if text in translations:
                return translations[text], 0.95
        
        # Try via intermediate (eng)
        if key not in self.TRANSLATIONS:
            # Try source -> eng -> target
            if source_lang != 'eng':
                eng_text, _ = self.translate(text, source_lang, 'eng', region)
                return self.translate(eng_text, 'eng', target_lang, region)
            if target_lang != 'eng':
                return self.translate(text, 'eng', target_lang, region)
        
        # Fallback: word-by-word translation
        return self._word_by_word_translate(text, source_lang, target_lang), 0.6
    
    def _word_by_word_translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Fallback word-by-word translation."""
        # Simple dictionary-based translation
        dictionary = {
            ('eng', 'ksl'): {
                'hello': 'HELLO',
                'goodbye': 'GOODBYE',
                'thank': 'THANK',
                'you': 'YOU',
                'please': 'PLEASE',
                'help': 'HELP',
                'me': 'ME',
                'i': 'I',
                'am': 'AM',
                'deaf': 'DEAF',
                'school': 'SCHOOL',
                'teacher': 'TEACHER',
                'student': 'STUDENT',
                'learn': 'LEARN',
                'sign': 'SIGN',
                'language': 'LANGUAGE',
                'water': 'WATER',
                'food': 'FOOD',
                'eat': 'EAT',
                'drink': 'DRINK',
                'go': 'GO',
                'come': 'COME',
                'where': 'WHERE',
                'what': 'WHAT',
                'who': 'WHO',
                'when': 'WHEN',
                'why': 'WHY',
                'how': 'HOW',
            }
        }
        
        key = (source_lang, target_lang)
        if key not in dictionary:
            return f"[{text}] (translation unavailable)"
        
        words = text.lower().split()
        translated_words = []
        
        for word in words:
            translated = dictionary[key].get(word, word.upper())
            translated_words.append(translated)
        
        # KSL gloss word order (simplified)
        if target_lang == 'ksl':
            # Basic word reordering for KSL grammar
            # Topic-comment structure
            return ' '.join(translated_words)
        
        return ' '.join(translated_words)
    
    def batch_translate(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[Tuple[str, float]]:
        """Translate multiple texts."""
        return [self.translate(t, source_lang, target_lang) for t in texts]
    
    def detect_language(self, text: str) -> str:
        """
        Detect if text is KSL gloss, English, or Kiswahili.
        
        Heuristics:
        - ALL CAPS with few words -> KSL
        - Swahili keywords -> Kiswahili
        - Otherwise -> English
        """
        # Check for KSL gloss (all caps, short)
        if text.isupper() and len(text.split()) <= 10:
            return 'ksl'
        
        # Check for Swahili keywords
        swahili_words = ['habari', 'asante', 'tafadhali', 'mzima', 'sijui', 'nitakusaidia']
        text_lower = text.lower()
        if any(word in text_lower for word in swahili_words):
            return 'swa'
        
        return 'eng'


def test_translator():
    """Test the translator."""
    translator = KSLTranslator()
    
    # Test cases
    test_cases = [
        ('HELLO YOU HOW?', 'ksl', 'eng'),
        ('Hello, how are you?', 'eng', 'ksl'),
        ('Thank you', 'eng', 'swa'),
        ('Asante', 'swa', 'eng'),
    ]
    
    print("KSL Translator Test Results:")
    print("=" * 50)
    
    for text, source, target in test_cases:
        result, confidence = translator.translate(text, source, target)
        print(f"{source.upper()} -> {target.upper()}:")
        print(f"  Input:  {text}")
        print(f"  Output: {result}")
        print(f"  Confidence: {confidence:.2%}")
        print()


if __name__ == '__main__':
    test_translator()
