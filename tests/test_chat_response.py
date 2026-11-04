from src.api.routes.chat import _content_to_text, _sse_event


def test_content_to_text_extracts_text_blocks():
    content = [
        {"type": "text", "text": "Primeira parte"},
        {"type": "image", "url": "ignored"},
        {"type": "text", "text": "Segunda parte"},
    ]

    assert _content_to_text(content) == "Primeira parte\nSegunda parte"


def test_content_to_text_preserves_plain_text():
    assert _content_to_text("Resposta do agente") == "Resposta do agente"


def test_sse_event_contains_json_payload():
    event = _sse_event("token", content="Olá")

    assert event == 'data: {"type": "token", "content": "Olá"}\n\n'
