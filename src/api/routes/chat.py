"""Chat API endpoints handling agent interactions."""

from fastapi import APIRouter, HTTPException, status
from langchain_core.messages import HumanMessage

from src.agent.graph import agent_executor
from src.api.schemas import ChatRequest, ChatResponse
from src.utils.logger import logger

chat_router = APIRouter(prefix="/chat", tags=["Chat"])


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
        agent_reply = final_state["messages"][-1].content

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
