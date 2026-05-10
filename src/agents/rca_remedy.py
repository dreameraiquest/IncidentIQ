from typing import List, Dict, Any
from langsmith import traceable
from src.models.incident import EvidenceCluster

@traceable(name="rca_agent")
def rca_agent(cluster: EvidenceCluster, rag_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    sources = [f"{c.get('title', 'Unknown Source')} ({c.get('source_file', 'unknown')})" for c in rag_chunks[:3]]
    return {
        "primary_cause": f"Detected operational anomaly in {cluster.candidate_category} matching signature '{cluster.signature}'.",
        "symptom_vs_cause": f"{cluster.candidate_category} signals are the primary hypothesized cause based on frequency ({cluster.signal_count}) and signal weight ({cluster.total_weight}).",
        "missing_evidence": "Trace correlation for upstream callers; exact config commit hash.",
        "rag_sources": sources,
    }

@traceable(name="remediation_agent")
def remediation_agent(cluster: EvidenceCluster, rag_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "immediate_actions": [
            f"Check status of {', '.join(cluster.affected_services[:3])} logs for '{cluster.signature}'",
            "Verify recent deployments or configuration changes in the last 15 minutes",
            "Check for saturation on storage and compute resources"
        ],
        "long_term_fix": f"Standardize error handling for {cluster.candidate_category} components and implement circuit breakers.",
        "safety_note": "Do not restart production database nodes without verified backup integrity and master/replica verification."
    }
