"""Chat API endpoints handling agent interactions."""

import json
from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from src.agent.graph import agent_executor
from src.api.schemas import ChatRequest
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


def _sse_event(event_type: str, **data: str) -> str:
    """Serialize one server-sent event as JSON."""
    return f"data: {json.dumps({'type': event_type, **data}, ensure_ascii=False)}\n\n"


async def _stream_agent_response(payload: ChatRequest) -> AsyncIterator[str]:
    """Stream text chunks produced by the LangGraph agent."""
    config = {"configurable": {"thread_id": payload.session_id}}
    initial_state = {"messages": [HumanMessage(content=payload.message)]}
    streamed_text = False

    try:
        async for message, metadata in agent_executor.astream(
            initial_state,
            config=config,
            stream_mode="messages",
        ):
            if metadata.get("langgraph_node") != "agent":
                continue

            text = _content_to_text(message.content)
            if text:
                streamed_text = True
                yield _sse_event("token", content=text)

        if not streamed_text:
            raise RuntimeError("The agent returned an empty response.")

        yield _sse_event("done", session_id=payload.session_id)
    except Exception as exc:
        logger.error(f"Error streaming chat turn: {str(exc)}", exc_info=True)
        yield _sse_event("error", detail=f"Erro ao processar a mensagem: {exc}")


@chat_router.post("", status_code=status.HTTP_200_OK)
async def send_message(payload: ChatRequest):
    """Streams the agent response using Server-Sent Events.

    Args:
        payload: Input message and session identifier.

    Returns:
        StreamingResponse: SSE stream with token, done, or error events.
    """
    logger.info(
        f"[POST /chat] Session: {payload.session_id} | Message: '{payload.message}'"
    )

    return StreamingResponse(
        _stream_agent_response(payload),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
