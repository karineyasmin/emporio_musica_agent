from src.api.routes.chat import _content_to_text


def test_content_to_text_extracts_text_blocks():
    content = [
        {"type": "text", "text": "Primeira parte"},
        {"type": "image", "url": "ignored"},
        {"type": "text", "text": "Segunda parte"},
    ]

    assert _content_to_text(content) == "Primeira parte\nSegunda parte"


def test_content_to_text_preserves_plain_text():
    assert _content_to_text("Resposta do agente") == "Resposta do agente"
