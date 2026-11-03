"""LLM client setup with primary Gemini provider and local fallback support."""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from src.config.config import settings
from src.utils.logger import logger


def get_llm(tools: list) -> BaseChatModel:
    """Instantiates the primary chat model bound with agent tools.

    Falls back to a local Ollama model if configured or if API initialization fails.

    Args:
        tools: List of LangChain tools to bind to the model for function calling.

    Returns:
        BaseChatModel: Configured language model instance ready for tool calling.
    """
    logger.info(f"Configuring primary LLM: {settings.GEMINI_MODEL}")

    try:
        if settings.GOOGLE_API_KEY:
            primary_llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.2,
            )
            return primary_llm.bind_tools(tools)

        logger.warning("GOOGLE_API_KEY is not set. Switching to Ollama provider.")
    except Exception as exc:
        logger.error(
            f"Failed to initialize Gemini model: {exc}. Falling back to Ollama."
        )

    # Local fallback via Ollama container
    fallback_llm = ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.2,
    )
    return fallback_llm.bind_tools(tools)
