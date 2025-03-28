from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional, Dict
from app.services.search_service import search_service
from app.core.auth import current_active_user
from app.models.user import User
from app.core.cache import cache
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class SearchFilters(BaseModel):
    document_type: Optional[str] = None
    language: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None

@router.get("/documents")
@cache(expire=300)  # Cache results for 5 minutes
async def search_documents(
    query: str = Query(..., min_length=2),
    filters: Optional[SearchFilters] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(current_active_user)
):
    """
    Advanced document search with filters and pagination.
    Features:
    - Full-text search with fuzzy matching
    - Highlighted matches
    - Filtering by multiple criteria
    - Access control based on user permissions
    """
    try:
        # Convert filters to elasticsearch format
        es_filters = {}
        if filters:
            if filters.document_type:
                es_filters["document_type"] = filters.document_type
            if filters.language:
                es_filters["language"] = filters.language
            if filters.tags:
                es_filters["tags"] = filters.tags
            if filters.status:
                es_filters["status"] = filters.status
            if filters.date_from or filters.date_to:
                es_filters["date_range"] = {
                    "gte": filters.date_from.isoformat() if filters.date_from else None,
                    "lte": filters.date_to.isoformat() if filters.date_to else None
                }
        
        # Add user-specific access control
        if not user.is_superuser:
            es_filters["access_control"] = {
                "user_id": user.id,
                "organization_id": user.organization_id
            }
        
        results = await search_service.search_documents(
            query=query,
            filters=es_filters,
            page=page,
            page_size=page_size
        )
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to search documents: " + str(e))

@router.get("/documents/{document_id}/similar")
@cache(expire=600)  # Cache results for 10 minutes
async def find_similar_documents(
    document_id: int,
    max_results: int = Query(5, ge=1, le=20),
    min_similarity: float = Query(0.5, ge=0, le=1),
    user: User = Depends(current_active_user)
):
    """
    Find similar documents using content-based similarity.
    """
    try:
        similar_docs = await search_service.suggest_similar_documents(
            document_id=document_id,
            max_results=max_results,
            min_similarity=min_similarity
        )
        return similar_docs
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to find similar documents: " + str(e))

@router.get("/autocomplete")
async def autocomplete_search(
    query: str = Query(..., min_length=1),
    field: str = Query(..., regex="^(title|content|tags)$"),
    user: User = Depends(current_active_user)
):
    """
    Provide search suggestions as user types.
    """
    try:
        suggestions = await search_service.get_suggestions(
            query=query,
            field=field
        )
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to provide autocomplete suggestions: " + str(e))

@router.post("/reindex")
async def reindex_documents(
    user: User = Depends(current_active_user)
):
    """
    Rebuild the search index (admin only).
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        task = await search_service.reindex_all_documents()
        return {"task_id": task.id, "status": "processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to reindex documents: " + str(e))
