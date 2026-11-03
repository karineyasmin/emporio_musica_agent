"""Vector store initialization and client management using langchain-postgres."""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from sqlalchemy import make_url

from src.config.config import settings
from src.utils.logger import logger

COLLECTION_NAME = "politicas_loja_docs"

embeddings_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True, "batch_size": 16},
)


def get_vector_store() -> PGVector:
    """Instantiates and returns a PGVector vector store client.

    Returns:
        PGVector: Connected vector store instance targeting PostgreSQL.
    """
    logger.info("Initializing PGVector client connection...")

    connection_url = settings.database_url

    parsed_url = make_url(connection_url)
    if parsed_url.drivername == "postgresql":
        connection_url = connection_url.replace(
            "postgresql://", "postgresql+psycopg://", 1
        )

    vector_store = PGVector(
        embeddings=embeddings_model,
        collection_name=COLLECTION_NAME,
        connection=connection_url,
        use_jsonb=True,
    )

    return vector_store
