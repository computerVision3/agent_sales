from typing import Sequence, TypedDict, Annotated, Union, Optional, Any
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph.message import add_messages

from langchain_postgres import PostgresChatMessageHistory


class AgentState(TypedDict):
    """
    The state of the agent.

    Attributes:
        messages: The conversation history of the agent. Annotated with `add_messages`
                  so new messages are automatically appended in LangGraph flows.
        number_of_steps: Number of reasoning or tool-invocation steps the agent has taken.
    """
    messages: Annotated[Sequence[Union[AIMessage, BaseMessage]], add_messages]
    # number_of_steps: int
    tool_outputs: Optional[dict[str, Any]]
    chat_history: Optional[PostgresChatMessageHistory]