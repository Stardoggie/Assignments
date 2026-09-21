from typing import Literal

from pydantic import BaseModel, Field


# Policy categories represented by the repository documents.
PolicyTopic = Literal[
    "account_and_billing",
    "returns_and_refunds",
    "shipping",
    "known_issues",
    "other",
]


class PolicySearch(BaseModel):
    """A first-pass analysis of a user's policy question.

    Identify the main policy topic and produce a concise search query.

    Preserve the meaning of the user's question. If the question is a
    contextual follow-up, use the conversation provided to make it standalone.

    Do not answer the question. Do not add facts that the user did not provide.
    """

    topic: PolicyTopic = Field(
        description=(
            "The policy category most closely related to the question. "
            "Use account_and_billing for plans, seats, invoices, and billing. "
            "Use returns_and_refunds for return windows, fees, and refunds. "
            "Use shipping for delivery times, costs, and lost shipments. "
            "Use known_issues for outages and documented product problems. "
            "Use other when none of the categories apply."
        )
    )

    summary: str = Field(
        description=(
            "A one-sentence standalone summary of what the user wants to know. "
            "Resolve words such as 'that', 'it', or 'members' using the "
            "conversation history provided."
        )
    )

    search_query: str = Field(
        description=(
            "A concise document-search query containing the important policy "
            "terms from the user's question. Do not answer the question."
        )
    )


class PolicyAnswer(BaseModel):
    """A document-grounded answer to a policy question.

    Answer ONLY from the policy excerpts provided to you. The excerpts are the
    company's official policy documents. Your own general knowledge is NOT a
    source and must not be used to fill a gap.

    If the excerpts do not cover the question, set `grounded` to false rather
    than producing a plausible answer.
    """

    grounded: bool = Field(
        description=(
            "True only if the provided policy excerpts directly support the "
            "answer. False if answering would require guessing or outside "
            "knowledge."
        )
    )

    answer: str = Field(
        description=(
            "A concise answer based only on the provided policy excerpts. "
            "If the excerpts do not cover the question, say that the provided "
            "documents do not cover it instead of guessing."
        )
    )

    sources: list[str] = Field(
        description=(
            "The exact policy filenames used to support the answer, copied "
            "from the 'source:' line of each excerpt. Use an empty list when "
            "the answer is not grounded."
        )
    )


class PolicyBrief(BaseModel):
    """The merged result of policy search preparation and grounded answering."""

    question: str
    search: PolicySearch
    answer: PolicyAnswer

    @property
    def should_refuse(self) -> bool:
        """Whether the assistant should refuse to answer the question."""

        return not self.answer.grounded

    @property
    def cited_sources(self) -> list[str]:
        """The policy documents used to support the answer."""

        return self.answer.sources