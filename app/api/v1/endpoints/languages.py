from fastapi import APIRouter, HTTPException
from typing import Dict, List
from app.services.language_service import LanguageService
from pydantic import BaseModel

router = APIRouter()
language_service = LanguageService()

class TranslationRequest(BaseModel):
    text: str
    source_language: str
    target_language: str

class LanguageAnalysisRequest(BaseModel):
    text: str
    language: str

@router.get("/supported")
async def get_supported_languages() -> Dict:
    """
    Get information about supported languages and available features.
    """
    return await language_service.get_language_support_info()

@router.post("/translate")
async def translate_text(request: TranslationRequest) -> Dict:
    """
    Translate text between supported languages.
    """
    try:
        translated_text = await language_service.translate_text(
            request.text,
            request.source_language,
            request.target_language
        )
        return {
            "translated_text": translated_text,
            "source_language": request.source_language,
            "target_language": request.target_language
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/analyze")
async def analyze_text(request: LanguageAnalysisRequest) -> Dict:
    """
    Analyze text structure for the specified language.
    """
    try:
        analysis = await language_service.analyze_language_structure(
            request.text,
            request.language
        )
        return {
            "analysis": analysis,
            "language": request.language
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/detect")
async def detect_language(text: str) -> Dict:
    """
    Detect the language of the input text.
    """
    detected_lang = await language_service.detect_language(text)
    return {
        "detected_language": detected_lang,
        "text_sample": text[:100] + "..." if len(text) > 100 else text
    }
