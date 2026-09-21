"""Nodes for preparing the initial policy search."""

from langchain_core.messages import BaseMessage

from ticket_assistant.graph.state import AssistantState
from ticket_assistant.rag import build_search_chain, format_query
from ticket_assistant.schemas import PolicySearch


def _message_text(message: BaseMessage) -> str:
    """Extract readable text from a LangChain message."""

    if isinstance(message.content, str):
        return message.content
    return str(message.content)


def prepare_search_node(state: AssistantState) -> dict:
    """Prepare the first search query for the current user question.

    Recent conversation history is included so contextual follow-ups can be
    rewritten as standalone policy searches.
    """

    question = state["question"]
    messages = state.get("messages", [])
    recent_messages = messages[-6:]
    conversation = "\n".join(
        f"{message.type}: {_message_text(message)}"
        for message in recent_messages
    )
    if conversation:
        search_input = (
            f"Recent conversation:\n{conversation}\n\n"
            f"Current question:\n{question}"
        )
    else:
        search_input = question
    search = build_search_chain().invoke(
        {
            "question": search_input,
        }
    )
    if not isinstance(search, PolicySearch):
        raise TypeError(
            "Search chain did not return a PolicySearch"
        )
    query = format_query(search)
    return {
        "search": search,
        "search_query": query,
        "retrieval_attempts": 0,
        "evidence": [
            f"prepared initial search query: {query!r}"
        ],
        "trace": ["prepare_search"]
    }