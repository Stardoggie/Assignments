"""Nodes for policy retrieval and query rewriting."""

from langchain_core.messages import HumanMessage, SystemMessage

from ticket_assistant.graph.state import AssistantState
from ticket_assistant.llm import get_chat_model
from ticket_assistant.prompts import REWRITE_PROMPT
from ticket_assistant.retriever import get_retriever


def retrieve_node(state: AssistantState) -> dict:
    """Retrieve policy excerpts using the current search query."""

    query = state.get("search_query") or state["question"]
    retriever = get_retriever(k=4)
    docs = retriever.invoke(query)
    attempts = state.get(
        "retrieval_attempts",
        0
    ) + 1

    return {
        "retrieved_docs": docs,
        "retrieval_attempts": attempts,
        "evidence": [
            f"retrieved {len(docs)} excerpts for {query!r}"
        ],
        "trace": [
            f"retrieve#{attempts}"
        ]
    }

def rewrite_query_node(state: AssistantState) -> dict:
    """Rewrite a weak query before the second retrieval attempt."""

    previous_query = (
        state.get("search_query")
        or state["question"]
    )
    search = state.get("search")
    topic = (
        search.topic
        if search is not None
        else "unknown"
    )
    summary = (
        search.summary
        if search is not None
        else state["question"]
    )
    response = get_chat_model(
        temperature=0.2
    ).invoke(
        [
            SystemMessage(REWRITE_PROMPT),
            HumanMessage(
                f"Original question:\n{state['question']}\n\n"
                f"Policy topic:\n{topic}\n\n"
                f"Question summary:\n{summary}\n\n"
                f"Previous weak query:\n{previous_query}\n\n"
                "Better search query:"
            )])

    rewritten_query = response.text.strip().strip('"')

    # Prevent a blank model response from creating a useless retry.
    if not rewritten_query:
        rewritten_query = state["question"]

    # Prevent the exact same query from being silently reused.
    if rewritten_query == previous_query:
        rewritten_query = (f"{topic} {summary}")
    return {
        "search_query": rewritten_query,
        "evidence": [
            f"rewrote search query: {rewritten_query!r}"
        ],
        "trace": ["rewrite_query"]
    }