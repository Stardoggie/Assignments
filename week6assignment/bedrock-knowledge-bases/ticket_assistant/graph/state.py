import operator
from typing import Annotated, NotRequired, TypedDict

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from ticket_assistant.schemas import PolicyAnswer, PolicySearch


class AssistantState(TypedDict):
    question: str
    messages: Annotated[list[AnyMessage], add_messages]
    search: NotRequired[PolicySearch | None]
    search_query: NotRequired[str]
    retrieved_docs: NotRequired[list[Document]]
    retrieval_attempts: int
    answer: NotRequired[PolicyAnswer | None]
    evidence: Annotated[list[str], operator.add]
    trace: Annotated[list[str], operator.add]