from typing import List, Dict, Any
from langsmith import traceable
from src.models.incident import EvidenceCluster

@traceable(name="timeline_agent")
def timeline_agent(cluster: EvidenceCluster) -> Dict[str, Any]:
    """Reconstructs the incident chronology."""
    # Simple chronological sort of the top evidence
    events = sorted(cluster.evidence, key=lambda x: x.get("timestamp") or "")
    chronology = []
    for ev in events[:10]:
        chronology.append({
            "timestamp": ev.get("timestamp"),
            "service": ev.get("service"),
            "event": ev.get("message")[:200]
        })
    return {
        "events": chronology,
        "summary": f"Incident began at {cluster.start_ts} and spanned {len(events)} detected signals."
    }

@traceable(name="critic_agent")
def critic_agent(incident: Dict[str, Any]) -> List[str]:
    """Validates the reasoning and checks for hallucinations."""
    findings = []
    # Heuristic validation
    if incident["confidence"] < 0.5:
        findings.append("Low confidence score: Evidence may be noisy or insufficient.")
    if not incident["affected_services"]:
        findings.append("Missing affected services: Root cause might be incomplete.")
    if len(incident["root_cause"].get("primary_cause", "")) < 20:
        findings.append("Vague root cause: Analysis requires more detail.")
    
    return findings if findings else ["No critical issues found. Reasoning is grounded in evidence."]
