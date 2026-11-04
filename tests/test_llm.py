from unittest.mock import Mock, patch

from src.agent.llm import get_llm
from src.config.config import settings


def test_get_llm_uses_gemini_when_api_key_is_configured():
    fake_bound_llm = Mock(name="gemini_bound")
    fake_gemini = Mock()
    fake_gemini.return_value.bind_tools.return_value = fake_bound_llm

    with patch("src.agent.llm.ChatGoogleGenerativeAI", fake_gemini):
        with patch.object(settings, "GOOGLE_API_KEY", "test-key"):
            result = get_llm([])

    fake_gemini.assert_called_once()
    assert result is fake_bound_llm


def test_get_llm_uses_ollama_when_google_key_is_missing():
    fake_bound_llm = Mock(name="ollama_bound")
    fake_ollama = Mock()
    fake_ollama.return_value.bind_tools.return_value = fake_bound_llm

    with patch("src.agent.llm.ChatOllama", fake_ollama):
        with patch.object(settings, "GOOGLE_API_KEY", ""):
            result = get_llm([])

    fake_ollama.assert_called_once_with(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.2,
    )
    assert result is fake_bound_llm
