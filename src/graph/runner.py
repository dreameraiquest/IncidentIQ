from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Tuple

import src.pipeline as pipeline
from src.graph.nodes import (
    GraphRunContext,
    cluster_evidence_node,
    export_results_node,
    extract_inputs_node,
    extract_signals_node,
    parse_raw_files_node,
    retrieve_runbooks_node,
    run_incident_agents_node,
    score_evals_node,
)


GraphNode = Callable[[pipeline.GraphState, GraphRunContext], pipeline.GraphState]


class IncidentGraphRunner:
    """LangGraph-compatible deterministic runner for the current backend.

    The node order is intentionally explicit so it can be lifted into a real
    LangGraph StateGraph without changing the backend contracts.
    """

    node_order: List[Tuple[str, GraphNode]] = [
        ("extract_inputs", extract_inputs_node),
        ("parse_raw_files", parse_raw_files_node),
        ("extract_signals", extract_signals_node),
        ("cluster_evidence", cluster_evidence_node),
        ("retrieve_runbooks", retrieve_runbooks_node),
        ("run_incident_agents", run_incident_agents_node),
        ("score_evals", score_evals_node),
        ("export_results", export_results_node),
    ]

    def __init__(self, options: dict, run_root: Path, output_root: Path) -> None:
        self.context = GraphRunContext(options=options, run_root=run_root, output_root=output_root)

    def run(self, state: pipeline.GraphState) -> pipeline.GraphState:
        for _, node in self.node_order:
            state = node(state, self.context)
        return state
