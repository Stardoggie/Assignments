from typing import cast

from ticket_assistant.graph.nodes.answer import route_after_answer
from ticket_assistant.schemas import PolicyAnswer
from ticket_assistant.graph.state import AssistantState


def test_grounded_answer_routes_to_finish():
    state = {
        "answer": PolicyAnswer(
            grounded=True,
            answer="Standard shipping takes 3–5 business days.",
            sources=["shipping-policy.md"]
        ),
        "retrieval_attempts": 1
    }

    assert route_after_answer(cast(AssistantState, state)) == "finish"


def test_ungrounded_first_answer_routes_to_rewrite():
    state = {
        "answer": PolicyAnswer(
            grounded=False,
            answer="The documents do not cover that question.",
            sources=[]
        ),
        "retrieval_attempts": 1
    }

    assert route_after_answer(cast(AssistantState, state)) == "rewrite_query"