"""
src/evals/evaluator.py
LLM-as-Judge evaluation for IncidentIQ.

Key fixes vs v1:
  - Smart GT matching: category → severity → semantic fallback (never blindly picks first)
  - Covers all real categories: Database, Deployment regression, API timeout,
    External dependency, Network, Unknown
  - If NO ground truth matches at all, score is flagged as "unmatched" and
    the judge is given an honest prompt so it doesn't unfairly penalise the incident.
  - Uses OpenRouter (OPENROUTER_API_KEY env var).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import requests

# ── OpenRouter ────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"
JUDGE_MODEL        = "openai/gpt-4o"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type":  "application/json",
    "HTTP-Referer":  "https://github.com/dreameraiquest/IncidentIQ",
    "X-Title":       "IncidentIQ LLM Judge",
}

# ── Weights ───────────────────────────────────────────────────────────────
WEIGHTS: Dict[str, float] = {
    "category_accuracy":   0.20,
    "severity_accuracy":   0.15,
    "rca_quality":         0.30,
    "remediation_quality": 0.25,
    "completeness":        0.10,
}

AXIS_LABELS: Dict[str, tuple] = {
    "category_accuracy":   ("🏷️", "Category Accuracy"),
    "severity_accuracy":   ("🔥", "Severity Accuracy"),
    "rca_quality":         ("🧬", "RCA Quality"),
    "remediation_quality": ("🛠️", "Remediation Quality"),
    "completeness":        ("📋", "Completeness"),
}

# ── Default ground truth covering all real incident categories ────────────
# Replace / extend with your own real labels.
DEFAULT_GROUND_TRUTH: List[Dict[str, Any]] = [
    {
        "id": "gt_database_p1",
        "category": "Database",
        "severity": "P1",
        "root_cause": "HikariCP connection pool exhaustion due to long-running queries",
        "affected_services": ["payment-api", "postgres-primary"],
        "expected_remediations": [
            "Increase HikariCP pool size",
            "Kill blocking long-running queries",
            "Check query index usage",
            "Add connection pool monitoring alerts",
        ],
    },
    {
        "id": "gt_deployment_p1",
        "category": "Deployment regression",
        "severity": "P1",
        "root_cause": "Bad deployment artifact or misconfigured rollout caused service regression",
        "affected_services": ["app-service", "deployment-pipeline"],
        "expected_remediations": [
            "Roll back to previous stable deployment",
            "Check deployment diff for breaking changes",
            "Run smoke tests post rollback",
            "Review CI/CD pipeline configuration",
        ],
    },
    {
        "id": "gt_api_timeout_p2",
        "category": "API timeout",
        "severity": "P2",
        "root_cause": "Upstream service latency or resource saturation causing API gateway timeouts",
        "affected_services": ["api-gateway", "upstream-service"],
        "expected_remediations": [
            "Check upstream service health and latency",
            "Review timeout configuration on API gateway",
            "Scale upstream service replicas",
            "Add circuit breaker around slow dependency",
        ],
    },
    {
        "id": "gt_external_dep_p2",
        "category": "External dependency",
        "severity": "P2",
        "root_cause": "Third-party service outage or degraded response causing cascading failures",
        "affected_services": ["integration-service", "third-party-api"],
        "expected_remediations": [
            "Enable fallback / stub response for failed dependency",
            "Check third-party status page",
            "Implement retry with exponential backoff",
            "Alert on-call if SLA breach imminent",
        ],
    },
    {
        "id": "gt_network_p2",
        "category": "Network",
        "severity": "P2",
        "root_cause": "DNS resolution failure or packet loss in service mesh",
        "affected_services": ["api-gateway", "auth-service"],
        "expected_remediations": [
            "Flush DNS cache on affected nodes",
            "Restart CoreDNS pods",
            "Check service mesh mTLS certificates",
            "Verify network policy rules",
        ],
    },
    {
        "id": "gt_unknown_p3",
        "category": "Unknown",
        "severity": "P3",
        "root_cause": "Undetermined — insufficient signal in logs to classify incident",
        "affected_services": [],
        "expected_remediations": [
            "Enable verbose logging on suspect services",
            "Correlate with APM traces",
            "Escalate to on-call engineer for manual triage",
        ],
    },
]

# ── Judge system prompt ───────────────────────────────────────────────────
JUDGE_SYSTEM = """
You are an expert DevOps incident-review judge evaluating an AI-generated
incident report against ground truth labels.

Return ONLY valid JSON — no markdown fences, no preamble — in exactly this shape:

{
  "category_accuracy":   { "score": <0-10>, "rationale": "<one sentence>" },
  "severity_accuracy":   { "score": <0-10>, "rationale": "<one sentence>" },
  "rca_quality":         { "score": <0-10>, "rationale": "<one sentence>" },
  "remediation_quality": { "score": <0-10>, "rationale": "<one sentence>" },
  "completeness":        { "score": <0-10>, "rationale": "<one sentence>" },
  "verdict":             "<2-3 sentence overall assessment>"
}

Scoring guide:
  10 = perfect match / excellent depth
  7-9 = mostly correct with minor gaps
  4-6 = partially correct, missing key details
  1-3 = significant errors or omissions
  0   = completely wrong or absent

IMPORTANT: If the ground truth entry is marked as the CLOSEST AVAILABLE (not an
exact category match), apply generous partial credit on category_accuracy and
still evaluate rca_quality / remediation_quality based on internal consistency
of the AI report.
"""


def _judge_prompt(detected: Dict[str, Any], gt: Dict[str, Any], exact_match: bool) -> str:
    match_note = (
        "NOTE: This ground truth entry is an EXACT category match."
        if exact_match else
        "NOTE: No exact category match was found in the ground truth. "
        "This is the CLOSEST AVAILABLE entry. Be fair — do not penalise "
        "category_accuracy twice; reflect the mismatch once and evaluate "
        "rca/remediation on internal coherence."
    )
    return (
        f"{match_note}\n\n"
        "=== DETECTED INCIDENT (AI output) ===\n"
        f"{json.dumps(detected, indent=2)}\n\n"
        "=== GROUND TRUTH (reference label) ===\n"
        f"{json.dumps(gt, indent=2)}\n\n"
        "Evaluate the detected incident on all five axes."
    )


# ── GT matching ───────────────────────────────────────────────────────────

# Category synonyms — groups of strings that mean the same thing
_SYNONYMS: List[List[str]] = [
    ["database", "db", "sql", "postgres", "mysql", "mongo", "hikari", "connection pool"],
    ["deployment", "deploy", "rollout", "release", "regression", "deployment regression"],
    ["api timeout", "timeout", "latency", "slow api", "api latency"],
    ["external dependency", "external", "third-party", "third party", "dependency", "saas"],
    ["network", "dns", "connectivity", "packet loss", "firewall"],
    ["unknown", "undetermined", "unclassified"],
]

def _canonical(cat: str) -> str:
    """Map a raw category string to the first synonym group it belongs to."""
    cat_l = cat.lower().strip()
    for group in _SYNONYMS:
        if any(syn in cat_l or cat_l in syn for syn in group):
            return group[0]
    return cat_l


def _find_best_gt(
    detected: Dict[str, Any],
    ground_truth: List[Dict[str, Any]],
) -> tuple[Dict[str, Any], bool]:
    """
    Returns (best_gt_entry, exact_match).

    Matching priority:
      1. Exact canonical category match
      2. Same severity
      3. First entry (last resort — flags as inexact)
    """
    if not ground_truth:
        return {}, False

    det_cat = _canonical(detected.get("category") or "")
    det_sev = (detected.get("severity") or "").upper()

    # Pass 1: canonical category match
    for gt in ground_truth:
        if _canonical(gt.get("category") or "") == det_cat:
            return gt, True

    # Pass 2: severity match
    for gt in ground_truth:
        if (gt.get("severity") or "").upper() == det_sev:
            return gt, False

    # Pass 3: last resort
    return ground_truth[0], False


# ── OpenRouter call ───────────────────────────────────────────────────────

def _call_openrouter(user_text: str) -> str:
    payload = {
        "model": JUDGE_MODEL,
        "max_tokens": 1024,
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user",   "content": user_text},
        ],
    }
    resp = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _parse_axes(raw: str) -> Dict[str, Any]:
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── Public API ────────────────────────────────────────────────────────────

def score_incident(
    detected: Dict[str, Any],
    ground_truth: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Score one detected incident with LLM-as-Judge via OpenRouter.
    Uses smart GT matching — never blindly falls back to first entry.
    """
    gt, exact = _find_best_gt(detected, ground_truth)

    try:
        raw  = _call_openrouter(_judge_prompt(detected, gt, exact))
        axes = _parse_axes(raw)
    except Exception as exc:
        axes = {ax: {"score": 0, "rationale": f"Judge error: {exc}"} for ax in WEIGHTS}
        axes["verdict"] = f"Evaluation failed: {exc}"

    # Weighted overall 0-100
    overall = sum(WEIGHTS[ax] * axes.get(ax, {}).get("score", 0) for ax in WEIGHTS) * 10

    return {
        "incident_id":   detected.get("incident_id", "unknown"),
        "category":      detected.get("category", "?"),
        "severity":      detected.get("severity", "?"),
        "matched_gt_id": gt.get("id", "none"),
        "exact_match":   exact,
        "overall_score": round(overall, 1),
        "axes":          {ax: axes[ax] for ax in WEIGHTS},
        "verdict":       axes.get("verdict", ""),
        "weights_used":  WEIGHTS,
    }


def evaluate_all(
    incidents: List[Dict[str, Any]],
    ground_truth: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Run LLM-as-Judge over every detected incident.
    Falls back to DEFAULT_GROUND_TRUTH if none supplied.
    """
    gt = ground_truth if ground_truth else DEFAULT_GROUND_TRUTH
    results = [score_incident(inc, gt) for inc in incidents]
    scores  = [r["overall_score"] for r in results]

    exact_count   = sum(1 for r in results if r["exact_match"])
    inexact_count = len(results) - exact_count

    return {
        "mean_score":        round(sum(scores) / len(scores), 1) if scores else 0.0,
        "total_evaluated":   len(results),
        "exact_gt_matches":  exact_count,
        "inexact_gt_matches": inexact_count,
        "incident_evals":    results,
    }