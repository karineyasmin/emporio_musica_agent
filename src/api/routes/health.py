"""Health check routes for service readiness and liveness."""

from fastapi import APIRouter, status
from sqlalchemy import text

from src.database.connection import engine
from src.utils.logger import logger

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Liveness probe: verifies that the application is running."""
    return {"status": "healthy", "service": "emporio-musica-api"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness probe: validates external dependencies such as the database."""
    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error(f"Database readiness check failed: {str(exc)}")
        db_status = "unavailable"
        return {"status": "unhealthy", "database": db_status}

    return {"status": "ready", "database": db_status}
