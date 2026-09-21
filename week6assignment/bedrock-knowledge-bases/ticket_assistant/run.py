"""Minimal command-line policy assistant."""

import uuid
from typing import Any, cast

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from ticket_assistant.graph.graph import build_graph
from ticket_assistant.schemas import PolicyAnswer, PolicySearch


def new_config() -> RunnableConfig:
    return {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        }
    }


def main() -> None:
    serializer = JsonPlusSerializer(
        allowed_msgpack_modules=[PolicyAnswer, PolicySearch]
    )
    memory = InMemorySaver(serde=serializer)
    app = build_graph(checkpointer=memory)
    config = new_config()
    print("Policy Assistant")
    print("Commands: /reset, /quit")
    while True:
        question = input("\nYou: ").strip()
        if question == "/quit":
            return
        if question == "/reset":
            config = new_config()
            print("Conversation reset.")
            continue
        if not question:
            continue
        result = app.invoke(
            cast(Any, {
                "question": question,
                "messages": [HumanMessage(content=question)],
                "retrieval_attempts": 0
            }),
            config
        )
        answer = result["answer"]
        print(f"\nAssistant: {answer.answer}")
        if answer.sources:
            print("Sources:")

            for source in answer.sources:
                print(f"- {source}")


if __name__ == "__main__":
    main()