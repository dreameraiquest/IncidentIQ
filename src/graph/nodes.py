from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import src.pipeline as pipeline


@dataclass(frozen=True)
class GraphRunContext:
    options: Dict[str, Any]
    run_root: Path
    output_root: Path


def _mark(state: pipeline.GraphState, step: str) -> pipeline.GraphState:
    state.graph_steps.append(step)
    return state


def extract_inputs_node(state: pipeline.GraphState, context: GraphRunContext) -> pipeline.GraphState:
    result = pipeline.extract_inputs(state.input_paths, context.run_root)
    state.copied_files = result.copied_files
    state.extracted_files = result.extracted_files
    state.skipped_files = result.skipped_files
    state.raw_files = result.raw_files
    state.ground_truth_files = result.ground_truth_files
    return _mark(state, "extract_inputs")


def parse_raw_files_node(state: pipeline.GraphState, context: GraphRunContext) -> pipeline.GraphState:
    state.events = pipeline.parse_raw_files([Path(path) for path in state.raw_files], context.run_root)
    return _mark(state, "parse_raw_files")


def extract_signals_node(state: pipeline.GraphState, context: GraphRunContext) -> pipeline.GraphState:
    state.signals = pipeline.extract_signals(state.events)
    return _mark(state, "extract_signals")


def cluster_evidence_node(state: pipeline.GraphState, context: GraphRunContext) -> pipeline.GraphState:
    state.clusters = pipeline.build_evidence_clusters(state.signals, context.options)
    return _mark(state, "cluster_evidence")


def retrieve_runbooks_node(state: pipeline.GraphState, context: GraphRunContext) -> pipeline.GraphState:
    state.rag_context = pipeline.retrieve_runbook_context(state.clusters, context.options)
    return _mark(state, "retrieve_runbooks")


def run_incident_agents_node(state: pipeline.GraphState, context: GraphRunContext) -> pipeline.GraphState:
    state.incidents, state.action_payloads = pipeline.run_incident_agents(
        state.run_id,
        state.clusters,
        state.rag_context,
    )
    return _mark(state, "run_incident_agents")


def score_evals_node(state: pipeline.GraphState, context: GraphRunContext) -> pipeline.GraphState:
    if context.options.get("run_evals", True):
        state.eval_summary = pipeline.score_evals(state.incidents, [Path(path) for path in state.ground_truth_files])
    else:
        state.eval_summary = {"enabled": False, "summary": None, "note": "Eval disabled by options."}
    return _mark(state, "score_evals")


def export_results_node(state: pipeline.GraphState, context: GraphRunContext) -> pipeline.GraphState:
    state.exports = pipeline.export_results(context.output_root, state)
    return _mark(state, "export_results")
