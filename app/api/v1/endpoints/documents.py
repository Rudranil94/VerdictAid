from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel
from app.services.document_analyzer import DocumentAnalyzer
from app.core.config import settings

router = APIRouter()
document_analyzer = DocumentAnalyzer()

class DocumentAnalysisResponse(BaseModel):
    simplified_content: str
    key_terms: List[dict]
    risks: dict
    language: str

@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(
    file: UploadFile = File(...),
    target_language: Optional[str] = "en"
):
    """
    Analyze a legal document and return simplified content, key terms, and risks.
    """
    if target_language not in settings.SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Language {target_language} not supported. Supported languages: {settings.SUPPORTED_LANGUAGES}"
        )
    
    content = await file.read()
    content = content.decode()
    
    # Process document
    simplified = await document_analyzer.simplify_document(content, target_language)
    key_terms = await document_analyzer.extract_key_terms(content)
    risks = await document_analyzer.analyze_risks(content)
    
    return DocumentAnalysisResponse(
        simplified_content=simplified,
        key_terms=key_terms,
        risks=risks,
        language=target_language
    )

@router.post("/generate")
async def generate_document(
    document_type: str,
    language: str,
    template_data: dict
):
    """
    Generate a legal document based on template and provided data.
    """
    # Implementation for document generation
    pass
