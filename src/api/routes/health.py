"""Health check routes for service readiness and liveness."""

from fastapi import APIRouter, status
from sqlalchemy import text

from src.database.connection import engine
from src.utils.logger import logger

health_router = APIRouter(tags=["Health"])


@health_router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Liveness probe: verifies that the FastAPI application is alive."""
    return {"status": "healthy", "service": "emporio-musica-api"}


@health_router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness probe: validates database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as exc:
        logger.error(f"Database readiness check failed: {str(exc)}")
        return {"status": "unhealthy", "database": "unavailable"}
