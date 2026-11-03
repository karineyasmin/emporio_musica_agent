"""Database connection and session management module."""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from src.config.config import settings
from src.utils.logger import logger

engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    """Initializes extensions such as pgvector and checks connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.info(
                "Extension 'vector' enabled and database connectivity verified."
            )
    except Exception as exc:
        logger.error(f"Failed to initialize database extension or connect: {str(exc)}")
        raise exc


def get_db() -> Generator[Session, None, None]:
    """Dependency helper for FastAPI routes requiring a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
