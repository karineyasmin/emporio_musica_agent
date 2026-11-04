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
    """Initializes database extensions, schema, and connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
        from src.database.models.category import Category
        from src.database.models.customer import Customer
        from src.database.models.order import Order, OrderItem
        from src.database.models.product import Product
        from src.database.models.promotion import Promotion

        _ = (Category, Customer, Order, OrderItem, Product, Promotion)
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verified.")
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
