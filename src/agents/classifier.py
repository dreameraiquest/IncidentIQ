from typing import List, Dict, Any
from langsmith import traceable
from src.models.incident import EvidenceCluster

@traceable(name="classifier_agent")
def classifier_agent(cluster: EvidenceCluster, rag_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    severity = cluster.severity_hint
    if cluster.total_weight >= 18 and cluster.candidate_category in {"Database", "Memory/CPU", "Disk/storage", "Deployment regression"}:
        severity = "P1"
    elif cluster.total_weight >= 9 and severity != "P1":
        severity = "P2"
    elif severity == "UNKNOWN":
        severity = "P3"
    
    confidence = min(0.95, 0.45 + min(cluster.total_weight, 30) / 60 + min(cluster.signal_count, 20) / 100)
    top_runbook = rag_chunks[0]["title"] if rag_chunks else "none"
    
    return {
        "category": cluster.candidate_category,
        "severity": severity,
        "confidence": round(confidence, 2),
        "title": f"{severity} {cluster.candidate_category} incident candidate: {cluster.signature}",
        "reasoning": f"{cluster.signal_count} signals and weight {cluster.total_weight} support {cluster.candidate_category}; top runbook match: {top_runbook}.",
    }
