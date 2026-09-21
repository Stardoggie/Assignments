"""Retrieval-augmented generation chains for the policy assistant."""

from operator import itemgetter
from typing import Any, cast

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    Runnable,
    RunnableLambda,
    RunnableParallel,
)

from ticket_assistant.llm import get_chat_model
from ticket_assistant.prompts import ANSWER_PROMPT, SEARCH_PROMPT
from ticket_assistant.retriever import get_retriever
from ticket_assistant.schemas import (
    PolicyAnswer,
    PolicyBrief,
    PolicySearch,
)


def format_query(search: PolicySearch) -> str:
    """Remove unnecessary details before retrieving policy documents.

    The structured search result contains the topic, a standalone summary,
    and a concise retrieval query. Combine those fields into the final query
    used by the in-memory retriever.
    """

    return (
        f"{search.topic} - "
        f"{search.summary} - "
        f"{search.search_query}"
    )


def format_docs(docs: list[Document]) -> str:
    """Turn retrieved documents into context for the model prompt."""

    blocks = []

    for doc in docs:
        metadata = doc.metadata

        header = f"source: {metadata.get('source', 'unknown')}"

        if metadata.get("section"):
            header += f" | section: {metadata['section']}"

        blocks.append(
            f"--- {header} ---\n"
            f"{doc.page_content.strip()}"
        )

    return "\n\n".join(blocks)


def enforce_grounding(answer: PolicyAnswer) -> PolicyAnswer:
    """Make sure the model actually produced a grounded policy answer.

    PolicyAnswer.sources uses the PolicySource Literal type, so Pydantic has
    already restricted citations to filenames that exist in the repository.
    """

    if not answer.grounded or not answer.sources:
        return answer.model_copy(
            update={
                "grounded": False,
                "answer": (
                    "The provided documents do not cover that question."
                ),
                "sources": [],
            }
        )

    return answer


def build_search_chain() -> Runnable:
    """Convert a user's policy question into a structured search plan."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SEARCH_PROMPT),
            (
                "human",
                "Prepare a document-search query for this policy question:\n\n"
                "{question}",
            ),
        ]
    )

    structured_model: Runnable[Any, PolicySearch] = cast(
        "Runnable[Any, PolicySearch]",
        get_chat_model()
        .with_structured_output(PolicySearch),
    )

    return prompt | structured_model


def build_rag_chain(k: int = 4) -> Runnable:
    """Build a standalone RAG chain for testing policy retrieval.

    This chain retrieves policy excerpts, sends them to the model, produces
    a structured PolicyAnswer, and enforces refusal when the result is not
    grounded.
    """

    retriever = get_retriever(k=k)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ANSWER_PROMPT),
            (
                "human",
                "Answer the question using only the policy excerpts below.\n\n"
                "Policy excerpts:\n"
                "{context}\n\n"
                "Question:\n"
                "{question}",
            ),
        ]
    )

    structured_model: Runnable[Any, PolicyAnswer] = cast(
        "Runnable[Any, PolicyAnswer]",
        get_chat_model()
        .with_structured_output(PolicyAnswer),
    )

    return (
        RunnableParallel(
            question=itemgetter("question"),
            context=(
                itemgetter("question")
                | retriever
                | RunnableLambda(format_docs)
            ),
        )
        | prompt
        | structured_model
        | RunnableLambda(enforce_grounding)
    )


def build_policy_chain() -> Runnable:
    """Combine search preparation and RAG answering.

    This is the policy-assistant equivalent of the on-call project's
    build_diagnosis_chain().
    """

    search_chain = build_search_chain()
    rag_chain = build_rag_chain()

    prepare_search = RunnableParallel(
        question=itemgetter("question"),
        search=search_chain,
    )

    generate_answer = RunnableParallel(
        question=itemgetter("question"),
        search=itemgetter("search"),
        answer=(
            itemgetter("search")
            | RunnableLambda(format_query)
            | RunnableLambda(
                lambda query: {
                    "question": query,
                }
            )
            | rag_chain
        ),
    )

    def merge_values(values: dict[str, Any]) -> PolicyBrief:
        return PolicyBrief(
            question=values["question"],
            search=values["search"],
            answer=values["answer"],
        )

    merge_result = RunnableLambda(merge_values)

    return prepare_search | generate_answer | merge_result


if __name__ == "__main__":
    print("=== TESTING RAW RAG CHAIN ===")

    rag_chain = build_rag_chain()

    rag_result = rag_chain.invoke(
        {
            "question": (
                "How long does a customer have to return an item, "
                "and is there a restocking fee?"
            )
        }
    )

    print(rag_result.model_dump_json(indent=2))

    print("\n=== TESTING COMPLETE POLICY CHAIN ===")

    policy_chain = build_policy_chain()

    policy_result = policy_chain.invoke(
        {
            "question": (
                "I ordered something a few weeks ago. How long do I have "
                "to send it back, and will I be charged?"
            )
        }
    )

    print(policy_result.model_dump_json(indent=2))

    print("\n=== TESTING UNSUPPORTED QUESTION ===")

    unsupported_result = policy_chain.invoke(
        {
            "question": (
                "What is the company's policy for purchasing cryptocurrency?"
            )
        }
    )

    print(unsupported_result.model_dump_json(indent=2))

