"""Chat API endpoints handling agent interactions."""

from collections.abc import Mapping, Sequence
from typing import Any

from fastapi import APIRouter, HTTPException, status
from langchain_core.messages import HumanMessage

from src.agent.graph import agent_executor
from src.api.schemas import ChatRequest, ChatResponse
from src.utils.logger import logger

chat_router = APIRouter(prefix="/chat", tags=["Chat"])


def _content_to_text(content: Any) -> str:
    """Convert LangChain text blocks into the API's string response format."""
    if isinstance(content, str):
        return content

    if isinstance(content, Sequence) and not isinstance(content, str | bytes):
        text_parts = []
        for part in content:
            part_text = _content_to_text(part).strip()
            if part_text:
                text_parts.append(part_text)
        return "\n".join(text_parts)

    if isinstance(content, Mapping):
        text = content.get("text")
        if isinstance(text, str):
            return text
        return ""

    return str(content)


@chat_router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def send_message(payload: ChatRequest):
    """Receives customer messages and returns responses processed by the agent.

    Args:
        payload: Input message and session identifier.

    Returns:
        ChatResponse: Structured response containing agent reply.
    """
    logger.info(
        f"[POST /chat] Session: {payload.session_id} | Message: '{payload.message}'"
    )

    try:
        config = {"configurable": {"thread_id": payload.session_id}}
        initial_state = {"messages": [HumanMessage(content=payload.message)]}

        # Execute cyclical graph until resolution
        final_state = agent_executor.invoke(initial_state, config=config)
        agent_reply = _content_to_text(final_state["messages"][-1].content).strip()
        if not agent_reply:
            raise RuntimeError("The agent returned an empty response.")

        return ChatResponse(
            response=agent_reply,
            session_id=payload.session_id,
        )
    except Exception as exc:
        logger.error(f"Error handling chat turn: {str(exc)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the request: {str(exc)}",
        ) from exc
