from unittest.mock import Mock, patch

from langchain_core.messages import AIMessage, HumanMessage

from src.agent.graph import call_model
from src.config.config import settings


def test_call_model_retries_with_ollama_when_primary_fails():
    primary = Mock()
    primary.invoke.side_effect = RuntimeError("429 RESOURCE_EXHAUSTED")
    fallback = Mock()
    fallback.invoke.return_value = AIMessage(content="Resposta local")
    state = {"messages": [HumanMessage(content="Olá")]}

    with patch.object(settings, "GOOGLE_API_KEY", "configured"):
        with patch("src.agent.graph.get_llm", return_value=primary):
            with patch("src.agent.graph.get_fallback_llm", return_value=fallback):
                result = call_model(state)

    assert result["messages"][0].content == "Resposta local"
    fallback.invoke.assert_called_once()


def test_call_model_raises_clear_error_when_both_models_fail():
    primary = Mock()
    primary.invoke.side_effect = RuntimeError("primary unavailable")
    fallback = Mock()
    fallback.invoke.side_effect = RuntimeError("ollama unavailable")
    state = {"messages": [HumanMessage(content="Olá")]}

    with patch.object(settings, "GOOGLE_API_KEY", "configured"):
        with patch("src.agent.graph.get_llm", return_value=primary):
            with patch("src.agent.graph.get_fallback_llm", return_value=fallback):
                try:
                    call_model(state)
                except RuntimeError as exc:
                    assert str(exc) == (
                        "The primary and fallback language models are unavailable."
                    )
                else:
                    raise AssertionError("Expected fallback failure to be raised")
