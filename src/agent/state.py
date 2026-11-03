"""State definition for the customer service agent graph."""

from collections.abc import Sequence
from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """Represents the complete conversational state of the agent.

    Attributes:
        messages: Sequence of chat messages exchanged between user and model,
            accumulated via the add_messages reducer.
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]
