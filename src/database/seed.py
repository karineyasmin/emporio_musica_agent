"""Database seeding script for structured CSV data and store policy embeddings."""

import glob
import json
import os

import pandas as pd
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import text

from src.database.connection import Base, engine, init_db
from src.database.models.category import Category
from src.database.models.customer import Customer
from src.database.models.order import Order, OrderItem
from src.database.models.product import Product
from src.database.models.promotion import Promotion
from src.database.vector_store import get_vector_store
from src.utils.logger import logger


def seed_relational_data():
    """Reads CSV files and populates PostgreSQL tables."""
    logger.info("Initializing relational schema...")
    Base.metadata.create_all(bind=engine)

    csv_mapping = {
        "categories": (Category, "data/*categories*.csv"),
        "customers": (Customer, "data/*customers*.csv"),
        "products": (Product, "data/*products*.csv"),
        "orders": (Order, "data/*orders*.csv"),
        "order_items": (OrderItem, "data/*order_items*.csv"),
        "promotions": (Promotion, "data/*promotions*.csv"),
    }

    with engine.begin() as conn:
        for table_name, (model_cls, file_pattern) in csv_mapping.items():
            matched_files = glob.glob(file_pattern)
            if not matched_files:
                logger.warning(f"File pattern {file_pattern} not found. Skipping...")
                continue

            file_path = matched_files[0]
            logger.info(f"Loading {file_path} into table {table_name}...")
            df = pd.read_csv(file_path)

            # Tratamento de colunas especiais
            if table_name == "products" and "specs" in df.columns:
                df["specs"] = df["specs"].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else x
                )

            conn.execute(text(f"TRUNCATE TABLE {model_cls.__tablename__} CASCADE;"))
            records = df.to_dict(orient="records")
            if records:
                conn.execute(model_cls.__table__.insert(), records)

    logger.info("Relational data successfully seeded.")


def seed_vector_data():
    """Parses politicas_da_loja.pdf and saves embeddings into pgvector."""
    pdf_candidates = glob.glob("data/*pol*ticas*.pdf")
    if not pdf_candidates:
        logger.warning("No store policy PDF found. Skipping vector seeding.")
        return

    pdf_path = pdf_candidates[0]
    logger.info("Loading policy manual into vector store...")
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n## ", "\n# ", "\n\n", "\n", " "],
    )
    split_docs = text_splitter.split_documents(docs)

    vector_store = get_vector_store()
    vector_store.add_documents(split_docs)
    logger.info(f"Ingested {len(split_docs)} policy chunks into pgvector.")


def main():
    """Main database seed execution."""
    init_db()
    seed_relational_data()
    seed_vector_data()
    logger.info("Seed process completed successfully!")


if __name__ == "__main__":
    main()
