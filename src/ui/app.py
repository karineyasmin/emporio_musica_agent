"""Streamlit frontend for the Emporio da Musica customer assistant."""

import os
from uuid import uuid4

import httpx
import streamlit as st


API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
CHAT_ENDPOINT = f"{API_URL}/chat"
HEALTH_ENDPOINT = f"{API_URL}/health"
REQUEST_TIMEOUT = httpx.Timeout(90.0, connect=5.0)


def initialize_session() -> None:
    """Create stable session state values for the current browser session."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"streamlit-{uuid4().hex}"
    if "messages" not in st.session_state:
        st.session_state.messages = []


def check_api_status() -> tuple[bool, str]:
    """Return the API availability and a user-facing status message."""
    try:
        response = httpx.get(HEALTH_ENDPOINT, timeout=5.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return False, f"API indisponível: {exc}"

    return True, "API conectada"


def send_message(message: str) -> str:
    """Send a message to the API and return the assistant response."""
    payload = {
        "message": message,
        "session_id": st.session_state.session_id,
    }

    try:
        response = httpx.post(
            CHAT_ENDPOINT,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        raise RuntimeError(
            f"A API retornou HTTP {exc.response.status_code}: {detail}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"Não foi possível contactar a API: {exc}") from exc
    except ValueError as exc:
        raise RuntimeError("A API retornou uma resposta inválida.") from exc

    assistant_response = data.get("response")
    if not isinstance(assistant_response, str) or not assistant_response.strip():
        raise RuntimeError("A API não retornou uma resposta de texto válida.")

    return assistant_response


def render_sidebar() -> None:
    """Render connection details and conversation controls."""
    with st.sidebar:
        st.header("Emporio da Música")
        st.caption("Assistente para instrumentos musicais")
        st.divider()

        is_available, status_message = check_api_status()
        if is_available:
            st.success(status_message)
        else:
            st.error(status_message)

        st.caption(f"API: `{API_URL}`")
        st.caption(f"Sessão: `{st.session_state.session_id}`")

        if st.button(
            "Limpar conversa",
            use_container_width=True,
            disabled=not st.session_state.messages,
        ):
            st.session_state.messages = []
            st.rerun()


def render_message_history() -> None:
    """Render persisted chat messages in chronological order."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def main() -> None:
    """Render the customer chat application."""
    st.set_page_config(
        page_title="Emporio da Música",
        page_icon="🎵",
        layout="centered",
    )
    initialize_session()

    st.markdown(
        """
        <style>
        .block-container { max-width: 860px; padding-top: 2rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("🎵 Emporio da Música")
    st.write(
        "Encontre instrumentos, consulte promoções e tire dúvidas sobre a loja."
    )

    render_sidebar()
    render_message_history()

    if not st.session_state.messages:
        st.info(
            "Experimente perguntar: **Quais violões estão disponíveis até R$ 1.000?**"
        )

    prompt = st.chat_input("Digite sua mensagem...")
    if not prompt or not prompt.strip():
        return

    user_message = prompt.strip()
    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Consultando o assistente..."):
            try:
                assistant_message = send_message(user_message)
            except RuntimeError as exc:
                st.error(str(exc))
                return

        st.markdown(assistant_message)
        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_message}
        )


if __name__ == "__main__":
    main()