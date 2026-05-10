import requests
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ── Issue 1 Fix: Fail loudly if URLs are missing ──────────────────
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
JIRA_WEBHOOK_URL  = os.getenv("JIRA_WEBHOOK_URL")

# Note: We don't raise ValueError here so the app doesn't crash on startup 
# if the user hasn't set them yet, but we will skip the calls with a clear message.

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

    # ── Slack via n8n ─────────────────────────────────────────
    if SLACK_WEBHOOK_URL:
        try:
            r = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
            results["slack"] = "Success" if r.status_code < 300 else f"Error {r.status_code}"
            print(f"[n8n Slack] {severity} — {r.status_code}")
        except Exception as e:
            results["slack"] = f"Failed: {str(e)}"
    else:
        results["slack"] = "Skipped — SLACK_WEBHOOK_URL not set in .env"

    # ── JIRA via n8n ──────────────────────────────────────────
    # Only send high-severity incidents to JIRA to avoid noise
    if JIRA_WEBHOOK_URL and severity.upper() in ["CRITICAL", "HIGH", "P1", "P2"]:
        try:
            r = requests.post(JIRA_WEBHOOK_URL, json=payload, timeout=10)
            results["jira"] = "Success" if r.status_code < 300 else f"Error {r.status_code}"
            print(f"[n8n JIRA] {severity} — {r.status_code}")
        except Exception as e:
            results["jira"] = f"Failed: {str(e)}"
    else:
        status = "Skipped — URL not set" if not JIRA_WEBHOOK_URL else f"Skipped — Low severity ({severity})"
        results["jira"] = status

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
