from celery import Celery
from app.core.config import settings
from app.services.document_analyzer import DocumentAnalyzer
from app.services.language_service import LanguageService
import json

# Initialize Celery
celery_app = Celery(
    "verdict_aid",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Initialize services
document_analyzer = DocumentAnalyzer()
language_service = LanguageService()

@celery_app.task(name="analyze_document_async")
def analyze_document_async(content: str, target_language: str = "en"):
    """
    Asynchronously analyze a document and return results.
    """
    # Detect source language
    source_language = language_service.detect_language(content)
    
    # Translate if necessary
    if source_language != target_language:
        content = language_service.translate_text(
            content,
            source_language,
            target_language
        )
    
    # Analyze document
    simplified = document_analyzer.simplify_document(content, target_language)
    key_terms = document_analyzer.extract_key_terms(content)
    risks = document_analyzer.analyze_risks(content)
    
    # Language structure analysis
    language_analysis = language_service.analyze_language_structure(
        content,
        target_language
    )
    
    return {
        "simplified_content": simplified,
        "key_terms": key_terms,
        "risks": risks,
        "language_analysis": language_analysis,
        "source_language": source_language,
        "target_language": target_language
    }

@celery_app.task(name="generate_document_async")
def generate_document_async(
    template_name: str,
    data: dict,
    language: str,
    output_format: str = "docx"
):
    """
    Asynchronously generate a document from template.
    """
    from app.services.document_generator import DocumentGenerator
    generator = DocumentGenerator()
    
    # Generate document
    document = generator.generate_document(
        template_name,
        data,
        language,
        output_format
    )
    
    return {
        "document": document,
        "format": output_format,
        "template": template_name,
        "language": language
    }

@celery_app.task(name="batch_process_documents")
def batch_process_documents(documents: list, target_language: str = "en"):
    """
    Process multiple documents in batch.
    """
    results = []
    
    for doc in documents:
        result = analyze_document_async.delay(
            doc["content"],
            target_language
        )
        results.append(result.get())
    
    return results
