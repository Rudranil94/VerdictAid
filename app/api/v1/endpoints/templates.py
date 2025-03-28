from fastapi import APIRouter, HTTPException
from typing import Dict, Optional
from pydantic import BaseModel
from app.services.document_generator import DocumentGenerator
from app.services.background_tasks import generate_document_async

router = APIRouter()
document_generator = DocumentGenerator()

class DocumentGenerationRequest(BaseModel):
    template_name: str
    data: Dict
    language: str
    output_format: str = "docx"

@router.get("/list")
async def list_templates(language: Optional[str] = None) -> Dict:
    """
    List available document templates, optionally filtered by language.
    """
    return await document_generator.list_available_templates(language)

@router.post("/generate")
async def generate_document(request: DocumentGenerationRequest) -> Dict:
    """
    Generate a document using a template.
    """
    try:
        # Start async task
        task = generate_document_async.delay(
            request.template_name,
            request.data,
            request.language,
            request.output_format
        )
        
        return {
            "task_id": task.id,
            "status": "processing",
            "template": request.template_name,
            "language": request.language,
            "output_format": request.output_format
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/{task_id}")
async def get_generation_status(task_id: str) -> Dict:
    """
    Get the status of an async document generation task.
    """
    task = generate_document_async.AsyncResult(task_id)
    
    if task.ready():
        if task.successful():
            return {
                "status": "completed",
                "result": task.get()
            }
        else:
            return {
                "status": "failed",
                "error": str(task.result)
            }
    
    return {
        "status": "processing",
        "task_id": task_id
    }
