from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.health import router as health_router
from src.config.config import settings
from src.database.connection import init_db
from src.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events management for startup and shutdown."""
    logger.info("Starting Emporio da Musica API Service...")
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Could not auto-init database on startup: {e}")
    yield
    logger.info("Shutting down Emporio da Musica API Service...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
