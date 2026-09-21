from ticket_assistant.graph.graph import build_graph
from ticket_assistant.graph.state import AssistantState
from langgraph.types import Command
import uuid
from typing import cast
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver

def print_steps(app,graph_input,config: RunnableConfig):
    for chunk in app.stream(graph_input, config, stream_mode="updates"):
        print("____________________________")
        print(chunk)
        if "__interrupt__" in chunk:
            return "interrupted"
    return "closed"


if __name__ == "__main__":
    checkpointer = InMemorySaver()
    app = build_graph(checkpointer=checkpointer)
    question= "what are the shipping service levels?"

    thread_id = uuid.uuid4()
    config: RunnableConfig = {
        "configurable": {
            "thread_id":thread_id
        }
    }
    initial_state = cast(AssistantState, {
        "question":question,
        "messages":[]  ,
          "evidence" :[],
        "retrieval_attempts": 0,
        "trace": [],
        })
    status: str = "new"
    while status != "closed":
        status = print_steps(app,initial_state,config)
        if status == "interrupted":
            response = input("approve / reject >") or "reject"
            initial_state = Command(resume=response)
    final_state = app.get_state(config).values
    for node in final_state.get("trace",[]):
        print(f"{node} ->")
