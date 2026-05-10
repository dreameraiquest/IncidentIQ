from __future__ import annotations

import src.pipeline as pipeline
from src.graph.runner import IncidentGraphRunner


LANGGRAPH_NODE_ORDER = [name for name, _ in IncidentGraphRunner.node_order]


def build_langgraph(runner: IncidentGraphRunner):
    """Build a LangGraph StateGraph with the same nodes as the backend runner.

    The production path currently uses IncidentGraphRunner's deterministic
    execution so the app keeps working even when optional LangGraph runtime
    behavior changes. This builder keeps the real node wiring in one place for
    teams that want to compile and run a LangGraph graph with the same context.
    """

    try:
        from langgraph.graph import END, StateGraph
    except Exception as exc:  # pragma: no cover - optional integration hook
        raise RuntimeError("LangGraph is not available in this environment.") from exc

    graph = StateGraph(pipeline.GraphState)
    previous = None
    for name, node in runner.node_order:
        graph.add_node(name, lambda state, _node=node: _node(state, runner.context))
        if previous is None:
            graph.set_entry_point(name)
        else:
            graph.add_edge(previous, name)
        previous = name
    if previous is not None:
        graph.add_edge(previous, END)
    return graph
