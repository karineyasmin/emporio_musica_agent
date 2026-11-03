"""RAG tool for retrieving policy documents, operating guidelines, and store procedures."""

from langchain_core.tools import tool

from src.database.vector_store import get_vector_store
from src.utils.logger import logger


@tool
def consultar_politicas_loja(query: str) -> str:
    """Queries the official policies, rules, and procedures manual of Emporio da Musica.

    Use this tool whenever the customer asks about:
    - Return, exchange, and remorse refund policies and deadlines
    - Physical store operating hours and official address
    - Payment methods, installment conditions, and cash/PIX discount rules
    - Shipping options, delivery estimates, tracking info, and fees
    - Legal and manufacturer warranty conditions
    - Data privacy and LGPD guidelines
    - General customer service guidelines and promotional rules

    Args:
        query: Search string or user question regarding store policies and procedures.

    Returns:
        str: Relevant text snippets extracted from the policy manual.
    """
    logger.info(f"[Tool: RAG] Searching store policies with query: '{query}'")
    try:
        vector_store = get_vector_store()
        results = vector_store.similarity_search(query, k=4)

        if not results:
            return "No specific instructions found in the policy manual for this query."

        context_parts = []
        for index, doc in enumerate(results, start=1):
            page_metadata = doc.metadata.get("page", "N/A")
            cleaned_content = doc.page_content.strip()
            context_parts.append(
                f"[Section {index} - Page {page_metadata}]:\n{cleaned_content}"
            )

        return "\n\n---\n\n".join(context_parts)
    except Exception as exc:
        logger.error(f"[Tool: RAG] Error querying vector store: {str(exc)}")
        return f"Error accessing store policies database: {str(exc)}"
