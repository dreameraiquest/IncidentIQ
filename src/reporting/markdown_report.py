from typing import List, Dict, Any
from src.models.incident import IncidentResult

def response_to_markdown(incidents: List[IncidentResult], summary: Dict[str, Any]) -> str:
    md = [f"# IncidentIQ Analysis Report\n"]
    md.append(f"**Run ID:** `{summary.get('run_id', 'unknown')}`  |  **Highest Severity:** `{summary.get('highest_severity', 'N/A')}`\n")
    md.append("## Executive Summary\n")
    md.append(f"- **Incidents Found:** {len(incidents)}")
    md.append(f"- **Signals Analyzed:** {summary.get('signals_found', 0)}")
    md.append(f"- **Events Parsed:** {summary.get('events_parsed', 0)}\n")
    
    for inc in incidents:
        md.append(f"## {inc.incident_id}: {inc.title}")
        md.append(f"- **Category:** {inc.category} | **Severity:** {inc.severity} | **Confidence:** {inc.confidence}")
        md.append(f"- **Services:** {', '.join(inc.affected_services)}")
        md.append(f"\n### Root Cause Analysis")
        md.append(inc.root_cause.get("primary_cause", "No primary cause found."))
        md.append(f"\n### Remediation")
        for action in inc.remediation.get("immediate_actions", []):
            md.append(f"- [ ] {action}")
        md.append("\n---\n")
        
    return "\n".join(md)
