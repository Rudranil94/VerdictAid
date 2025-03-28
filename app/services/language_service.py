from typing import Dict, List, Optional
from deep_translator import GoogleTranslator
import spacy
from app.core.config import settings

class LanguageService:
    def __init__(self):
        self.supported_languages = settings.SUPPORTED_LANGUAGES
        self.nlp_models = {}
        
    async def load_language_model(self, language: str):
        """Load spaCy language model for specific language."""
        if language not in self.nlp_models:
            try:
                if language == "en":
                    model = "en_core_web_sm"
                elif language == "es":
                    model = "es_core_news_sm"
                elif language == "fr":
                    model = "fr_core_news_sm"
                elif language == "de":
                    model = "de_core_news_sm"
                else:
                    raise ValueError(f"No spaCy model available for language: {language}")
                    
                self.nlp_models[language] = spacy.load(model)
            except OSError:
                # Download model if not available
                spacy.cli.download(model)
                self.nlp_models[language] = spacy.load(model)
    
    async def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Translate text between supported languages.
        """
        if source_lang not in self.supported_languages or target_lang not in self.supported_languages:
            raise ValueError("Unsupported language combination")
            
        if source_lang == target_lang:
            return text
            
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        return translator.translate(text)
    
    async def analyze_language_structure(
        self,
        text: str,
        language: str
    ) -> Dict:
        """
        Analyze text structure using spaCy for the specified language.
        """
        await self.load_language_model(language)
        nlp = self.nlp_models[language]
        
        doc = nlp(text)
        
        analysis = {
            "entities": [(ent.text, ent.label_) for ent in doc.ents],
            "sentences": [sent.text for sent in doc.sents],
            "key_phrases": [(chunk.text, chunk.root.pos_) for chunk in doc.noun_chunks],
        }
        
        return analysis
    
    async def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text.
        Returns ISO 639-1 language code.
        """
        # For simplicity, using spaCy's language detection
        # In production, consider using dedicated language detection libraries
        # like langdetect or polyglot
        
        max_score = 0
        detected_lang = "en"  # default
        
        for lang in self.supported_languages:
            if lang in self.nlp_models:
                nlp = self.nlp_models[lang]
                doc = nlp(text[:1000])  # Use first 1000 chars for efficiency
                score = doc._.language["score"]
                if score > max_score:
                    max_score = score
                    detected_lang = lang
                    
        return detected_lang
    
    async def get_language_support_info(self) -> Dict:
        """
        Get information about supported languages and available features.
        """
        return {
            "supported_languages": self.supported_languages,
            "translation_pairs": [
                {"source": src, "target": tgt}
                for src in self.supported_languages
                for tgt in self.supported_languages
                if src != tgt
            ],
            "nlp_support": {
                lang: lang in self.nlp_models
                for lang in self.supported_languages
            }
        }
