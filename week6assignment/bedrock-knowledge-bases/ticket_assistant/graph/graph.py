"""Build and compile the policy-assistant LangGraph."""

from langgraph.graph import END, START, StateGraph

from ticket_assistant.graph.nodes.answer import answer_node,finish_node,refuse_node,route_after_answer

from ticket_assistant.graph.nodes.retrieval import retrieve_node,rewrite_query_node
from ticket_assistant.graph.nodes.search import prepare_search_node
from ticket_assistant.graph.state import AssistantState


def build_graph(checkpointer=None):
    """Build and compile the policy-assistant graph."""

    graph = StateGraph(AssistantState)
    graph.add_node("prepare_search",prepare_search_node)
    graph.add_node("retrieve",retrieve_node)
    graph.add_node( "answer",answer_node)
    graph.add_node("rewrite_query",rewrite_query_node)
    graph.add_node("finish",finish_node)
    graph.add_node("refuse", refuse_node)
    # Initial path
    graph.add_edge(START,"prepare_search")
    graph.add_edge("prepare_search","retrieve")
    graph.add_edge("retrieve","answer")
    graph.add_conditional_edges("answer",route_after_answer,{
            "finish": "finish",
            "rewrite_query": "rewrite_query",
            "refuse": "refuse",
        })
    graph.add_edge("rewrite_query","retrieve")
    graph.add_edge("finish",END)
    graph.add_edge( "refuse",END)
    return graph.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    app = build_graph()
    print(app.get_graph().draw_mermaid())