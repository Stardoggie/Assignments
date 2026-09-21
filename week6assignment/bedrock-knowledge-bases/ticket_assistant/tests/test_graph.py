from ticket_assistant.graph.graph import build_graph


def test_graph_has_expected_nodes():
    app = build_graph()
    graph = app.get_graph()
    assert set(graph.nodes) == {
        "__start__",
        "prepare_search",
        "retrieve",
        "answer",
        "rewrite_query",
        "finish",
        "refuse",
        "__end__"
    }


def test_graph_has_expected_edges():
    app = build_graph()
    graph = app.get_graph()

    edges = {
        (edge.source, edge.target)
        for edge in graph.edges
    }
    expected_edges = {
        ("__start__", "prepare_search"),
        ("prepare_search", "retrieve"),
        ("retrieve", "answer"),
        ("answer", "finish"),
        ("answer", "rewrite_query"),
        ("answer", "refuse"),
        ("rewrite_query", "retrieve"),
        ("finish", "__end__"),
        ("refuse", "__end__")
    }
    assert edges == expected_edges

def test_graph_contains_retry_cycle():
    app = build_graph()
    graph = app.get_graph()
    edges = {
        (edge.source, edge.target)
        for edge in graph.edges
    }
    assert ("answer", "rewrite_query") in edges
    assert ("rewrite_query", "retrieve") in edges
    assert ("retrieve", "answer") in edges