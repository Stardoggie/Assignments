"""Nodes for answering, routing, finishing, and refusing."""

from typing import cast

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ticket_assistant.graph.state import AssistantState
from ticket_assistant.llm import get_chat_model
from ticket_assistant.prompts import ANSWER_PROMPT
from ticket_assistant.rag import enforce_grounding, format_docs
from ticket_assistant.schemas import PolicyAnswer


MAX_RETRIEVAL_ATTEMPTS = 2


def answer_node(state: AssistantState) -> dict:
    """Produce a structured answer from the retrieved policy excerpts."""

    docs = state.get("retrieved_docs", [])
    if not docs:
        answer = PolicyAnswer(
            grounded=False,
            answer=(
                "The provided documents do not cover that question."
            ),
            sources=[]
        )
        return {
            "answer": answer,
            "evidence": [
                "answer ungrounded because retrieval returned no documents"
            ],
            "trace": ["answer:no_documents"]
        }
    context = format_docs(docs)
    raw_answer = (
        get_chat_model()
        .with_structured_output(PolicyAnswer)
        .invoke(
            [
                SystemMessage(ANSWER_PROMPT),
                HumanMessage(
                    "Answer the question using only the policy excerpts "
                    "below.\n\n"
                    f"Policy excerpts:\n{context}\n\n"
                    f"Question:\n{state['question']}"
                )
            ]
        )
    )
    answer = enforce_grounding(
        cast(PolicyAnswer, raw_answer)
    )
    return {
        "answer": answer,
        "evidence": [
            f"answer grounded={answer.grounded} "
            f"sources={answer.sources}"
        ],
        "trace": ["answer"]
    }

def route_after_answer(state: AssistantState) -> str:
    """Finish grounded answers, retry weak searches, or refuse."""

    answer = state.get("answer")
    attempts = state.get(
        "retrieval_attempts",
        0
    )
    if answer and answer.grounded:
        return "finish"
    if attempts < MAX_RETRIEVAL_ATTEMPTS:
        return "rewrite_query"
    return "refuse"

def finish_node(state: AssistantState) -> dict:
    """Add the final grounded answer to conversation history."""

    answer = state.get("answer")
    if answer is None:
        raise ValueError(
            "finish reached without a PolicyAnswer"
        )
    if not answer.grounded:
        raise ValueError(
            "finish reached with an ungrounded PolicyAnswer"
        )
    return {
        "messages": [
            AIMessage(content=answer.answer)
        ],
        "evidence": [
            f"finished with sources={answer.sources}"
        ],
        "trace": ["finish"]
    }

def refuse_node(state: AssistantState) -> dict:
    """Return a deterministic refusal after retrieval attempts are exhausted."""

    answer = PolicyAnswer(
        grounded=False,
        answer=(
            "The provided documents do not cover that question."
        ),
        sources=[],
    )
    return {
        "answer": answer,
        "messages": [
            AIMessage(content=answer.answer)
        ],
        "evidence": [
            "refused after retrieval attempts were exhausted"
        ],
        "trace": ["refuse"]
    }