from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import settings
from app.api.v1.api import api_router
from app.db.session import get_async_session
from app.core.redis import get_redis

app = FastAPI(
    title="Verdict Aid",
    description="Your Multilingual AI Legal Companion",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check endpoint
@app.get("/health")
async def health_check(
    session: AsyncSession = Depends(get_async_session),
    redis = Depends(get_redis)
):
    status = {
        "status": "healthy",
        "service": "Verdict Aid",
        "version": settings.VERSION,
        "api_version": "v1",
        "components": {
            "database": "healthy",
            "redis": "healthy"
        }
    }
    
    try:
        # Test database connection
        result = await session.execute("SELECT 1")
        if not result.scalar():
            raise Exception("Database connection failed")
    except Exception as e:
        status["components"]["database"] = f"unhealthy: {str(e)}"
        status["status"] = "unhealthy"
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    try:
        # Test Redis connection
        await redis.ping()
    except Exception as e:
        status["components"]["redis"] = f"unhealthy: {str(e)}"
        status["status"] = "unhealthy"
        raise HTTPException(status_code=503, detail="Redis connection failed")
    
    return status
