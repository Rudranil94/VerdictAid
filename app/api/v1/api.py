from fastapi import APIRouter
from app.api.v1.endpoints import documents, languages, templates

api_router = APIRouter()

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]
)

api_router.include_router(
    languages.router,
    prefix="/languages",
    tags=["languages"]
)

api_router.include_router(
    templates.router,
    prefix="/templates",
    tags=["templates"]
)
