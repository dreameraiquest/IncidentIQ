import requests
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

WEBHOOK_ALIASES = {
    "slack": ("SLACK_WEBHOOK_URL", "N8N_SLACK_WEBHOOK_URL"),
    "jira": ("JIRA_WEBHOOK_URL", "N8N_JIRA_WEBHOOK_URL"),
}


def _get_webhook_url(kind: str) -> tuple[str, str]:
    """Read webhook secrets at call time so Hugging Face restarts pick them up cleanly."""
    for name in WEBHOOK_ALIASES[kind]:
        value = os.getenv(name)
        if value:
            return value, name
    return "", WEBHOOK_ALIASES[kind][0]


def _post_webhook(kind: str, payload: Dict[str, Any], timeout: int) -> str:
    url, env_name = _get_webhook_url(kind)
    if not url:
        aliases = ", ".join(WEBHOOK_ALIASES[kind])
        return f"Skipped - missing Space secret ({aliases})"

    outbound_payload = payload
    if kind == "slack" and "hooks.slack.com/" in url:
        outbound_payload = {
            "text": (
                f"*IncidentIQ Alert*\\n"
                f"*Severity:* {payload.get('severity')}\\n"
                f"*Service:* {payload.get('service')}\\n"
                f"*Symptom:* {payload.get('symptom')}\\n"
                f"*Next step:* {payload.get('nextsteps')}"
            )
        }

    try:
        response = requests.post(url, json=outbound_payload, timeout=timeout)
    except requests.RequestException as exc:
        return f"Failed - request error via {env_name}: {exc}"

    if response.status_code < 300:
        return f"Success via {env_name}"

    body = response.text.replace("\n", " ").strip()
    if len(body) > 180:
        body = body[:177] + "..."
    detail = f": {body}" if body else ""
    return f"Error {response.status_code} via {env_name}{detail}"

def send_incident_to_n8n(incident: Dict[str, Any]) -> Dict[str, str]:
    """Send a single incident to n8n webhooks for Slack + JIRA dispatch."""

    severity  = incident.get("severity", "UNKNOWN")
    title     = incident.get("title", "Unknown Symptom")
    
    # ── Issue 3 Fix: Ensure affected_services is handled ───────────
    services  = incident.get("affected_services", [])
    service   = ", ".join(services) if services else incident.get("category", "Unknown Service")
    
    remediation = incident.get("remediation", {})
    # Handle both dictionary and direct list types for robustness
    if isinstance(remediation, dict):
        actions = remediation.get("immediate_actions", [])
    elif isinstance(remediation, list):
        actions = remediation
    else:
        actions = []
        
    nextsteps = actions[0] if actions else "Check logs for details"

    payload = {
        "severity":  severity,
        "service":   service,
        "symptom":   title,
        "nextsteps": nextsteps
    }

    results = {}

    # Slack via n8n
    results["slack"] = _post_webhook("slack", payload, timeout=10)

    # JIRA via n8n
    # Only send high-severity incidents to JIRA to avoid noise
    if severity.upper() in ["CRITICAL", "HIGH", "P1", "P2"]:
        results["jira"] = _post_webhook("jira", payload, timeout=15)
    else:
        results["jira"] = f"Skipped - low severity ({severity})"

    return results

def notify_all_incidents(incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Trigger n8n for all incidents. Returns per-incident status."""
    results = []
    for inc in incidents:
        res = send_incident_to_n8n(inc)
        results.append({
            "incident_id": inc.get("incident_id", "unknown"),
            "title":       inc.get("title", ""),
            "status":      res
        })
    return results
