from ticket_assistant.graph.nodes.answer import (
    MAX_RETRIEVAL_ATTEMPTS,
    route_after_answer
)
from ticket_assistant.schemas import PolicyAnswer
from ticket_assistant.graph.state import AssistantState


def test_exhausted_attempts_route_to_refusal():
    state: AssistantState = {
        "question": "",
        "messages": [],
        "evidence": [],
        "trace": [],
        "answer": PolicyAnswer(
            grounded=False,
            answer="The documents do not cover that question.",
            sources=[]
        ),
        "retrieval_attempts": MAX_RETRIEVAL_ATTEMPTS
    }

    assert route_after_answer(state) == "refuse"


def test_attempts_above_limit_still_route_to_refusal():
    state: AssistantState = {
        "question": "",
        "messages": [],
        "evidence": [],
        "trace": [],
        "answer": PolicyAnswer(
            grounded=False,
            answer="The documents do not cover that question.",
            sources=[]
        ),
        "retrieval_attempts": MAX_RETRIEVAL_ATTEMPTS + 5
    }

    assert route_after_answer(state) == "refuse"