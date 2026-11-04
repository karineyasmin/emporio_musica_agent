from types import SimpleNamespace
from unittest.mock import patch

from src.agent.tools.rag_tools import consultar_politicas_loja


def test_policy_tool_formats_similarity_results():
    documents = [
        SimpleNamespace(
            page_content="Prazo de devolução: 7 dias.",
            metadata={"page": 3},
        )
    ]
    vector_store = SimpleNamespace(similarity_search=lambda query, k: documents)

    with patch(
        "src.agent.tools.rag_tools.get_vector_store",
        return_value=vector_store,
    ):
        result = consultar_politicas_loja.invoke({"query": "devolução"})

    assert "[Section 1 - Page 3]:" in result
    assert "Prazo de devolução: 7 dias." in result


def test_policy_tool_reports_when_no_documents_match():
    vector_store = SimpleNamespace(similarity_search=lambda query, k: [])

    with patch(
        "src.agent.tools.rag_tools.get_vector_store",
        return_value=vector_store,
    ):
        result = consultar_politicas_loja.invoke({"query": "assunto desconhecido"})

    assert result == "No specific instructions found in the policy manual for this query."
