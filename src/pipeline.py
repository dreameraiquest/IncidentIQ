import csv
import hashlib
import json
import os
import re
import shutil
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
from dateutil import parser as dtparser
from pydantic import BaseModel, Field


WORK_ROOT = Path(
    os.getenv(
        "INCIDENTIQ_WORK_ROOT",
        "/content/incidentiq_work" if Path("/content").exists() else "/tmp/incidentiq_work",
    )
)
WORK_ROOT.mkdir(parents=True, exist_ok=True)

DEFAULT_OPTIONS = {
    "enable_llm": os.getenv("ENABLE_LLM_MODE", "false").lower() == "true",
    "enable_rag": os.getenv("ENABLE_RAG_MODE", "true").lower() == "true",
    "preview_only": os.getenv("ENABLE_PREVIEW_MODE", "true").lower() == "true",
    "enable_real_integrations": os.getenv("ENABLE_REAL_INTEGRATIONS", "false").lower() == "true",
    "run_evals": os.getenv("ENABLE_EVAL_MODE", "true").lower() == "true",
    "max_clusters": int(os.getenv("MAX_CLUSTERS", "25")),
    "max_evidence_per_cluster": int(os.getenv("MAX_EVIDENCE_PER_CLUSTER", "25")),
    "time_window_minutes": int(os.getenv("DEFAULT_TIME_WINDOW_MINUTES", "5")),
}

ALLOWED_SUFFIXES = {".zip", ".jsonl", ".log", ".txt", ".json", ".csv"}
CATEGORY_VALUES = [
    "Database",
    "Network",
    "Authentication",
    "Memory/CPU",
    "Deployment regression",
    "API timeout",
    "Queue backlog",
    "Disk/storage",
    "External dependency",
    "Unknown",
]
SEVERITY_ORDER = {"P1": 1, "P2": 2, "P3": 3, "P4": 4, "UNKNOWN": 5}


class AnalysisRequest(BaseModel):
    run_id: str
    uploaded_paths: List[str]
    options: Dict[str, Any] = Field(default_factory=dict)


class LogEvent(BaseModel):
    source_file: str
    line_no: int
    timestamp: Optional[str] = None
    level: str = "UNKNOWN"
    service: str = "unknown"
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    host: Optional[str] = None
    namespace: Optional[str] = None
    pod: Optional[str] = None
    container: Optional[str] = None
    raw_line: str
    parse_status: str = "parsed"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SignalMatch(BaseModel):
    signal_type: str
    rule_id: str
    signature: str
    weight: float
    severity_hint: str = "UNKNOWN"
    source_file: str
    line_no: int
    timestamp: Optional[str] = None
    service: str = "unknown"
    level: str = "UNKNOWN"
    message: str
    trace_id: Optional[str] = None


class EvidenceCluster(BaseModel):
    cluster_id: str
    candidate_category: str
    signature: str
    affected_services: List[str]
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    window: str = "unknown-window"
    signal_count: int = 0
    total_weight: float = 0.0
    severity_hint: str = "UNKNOWN"
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    rule_ids: List[str] = Field(default_factory=list)
    trace_ids: List[str] = Field(default_factory=list)
    summary: str = ""


class IncidentResult(BaseModel):
    incident_id: str
    cluster_id: str
    category: str
    severity: str
    confidence: float
    title: str
    affected_services: List[str]
    symptom_vs_cause: str
    timeline: Dict[str, Any]
    root_cause: Dict[str, Any]
    remediation: Dict[str, Any]
    critic_findings: List[str]
    evidence_grounded: bool = True
    approval_status: str = "PENDING_HUMAN_APPROVAL"


class TicketPayload(BaseModel):
    system: str = "jira-preview"
    create_issue: bool = True
    project_key: str = "OPS"
    title: str
    priority: str
    labels: List[str]
    description: str
    evidence: List[str]
    approval_status: str = "PREVIEW_ONLY"


class SlackPayload(BaseModel):
    channel: str = "#devops-incidents"
    send_message: bool = True
    title: str
    body: str
    approval_status: str = "PREVIEW_ONLY"


class CookbookPayload(BaseModel):
    title: str
    steps: List[str]
    validation: List[str]
    safety_notes: List[str]


class ActionPayload(BaseModel):
    run_id: str
    approval_status: str
    incident_id: str
    severity: str
    category: str
    ticket: TicketPayload
    slack: SlackPayload
    cookbook: CookbookPayload


class AnalysisResponse(BaseModel):
    run_id: str
    status: str
    highest_severity: str = "UNKNOWN"
    summary: Dict[str, Any] = Field(default_factory=dict)
    incidents: List[IncidentResult] = Field(default_factory=list)
    slack_payloads: List[SlackPayload] = Field(default_factory=list)
    jira_payloads: List[TicketPayload] = Field(default_factory=list)
    cookbooks: List[CookbookPayload] = Field(default_factory=list)
    reports: Dict[str, str] = Field(default_factory=dict)
    eval: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class GraphState(BaseModel):
    run_id: str
    input_paths: List[str] = Field(default_factory=list)
    runtime_root: str = ""
    raw_files: List[str] = Field(default_factory=list)
    ground_truth_files: List[str] = Field(default_factory=list)
    events: List[LogEvent] = Field(default_factory=list)
    signals: List[SignalMatch] = Field(default_factory=list)
    clusters: List[EvidenceCluster] = Field(default_factory=list)
    rag_context: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    incidents: List[IncidentResult] = Field(default_factory=list)
    action_payloads: List[ActionPayload] = Field(default_factory=list)
    eval_summary: Optional[Dict[str, Any]] = None
    exports: Dict[str, str] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


def model_to_dict(obj: Any) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return dict(obj)


def new_run_id() -> str:
    return "run_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def safe_copy_uploads(files_or_paths: Iterable[Any], run_id: str) -> List[str]:
    upload_dir = WORK_ROOT / "uploads" / run_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for idx, item in enumerate(files_or_paths or []):
        if item is None:
            continue
        if isinstance(item, (str, Path)):
            src = Path(item)
        elif isinstance(item, dict) and item.get("name"):
            src = Path(item["name"])
        elif hasattr(item, "name"):
            src = Path(str(item.name))
        else:
            dst = upload_dir / f"uploaded_{idx}.log"
            data = item if isinstance(item, (bytes, bytearray)) else bytes(str(item), "utf-8")
            dst.write_bytes(data)
            saved.append(str(dst))
            continue
        if not src.exists():
            raise FileNotFoundError(f"Uploaded path not found: {src}")
        dst = upload_dir / src.name
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        saved.append(str(dst))
    return saved


def safe_extract_zip(zip_path: Path, dest_root: Path) -> List[Path]:
    extracted = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            member_name = member.filename.replace("\\", "/")
            if member_name.endswith("/"):
                continue
            target = (dest_root / member_name).resolve()
            if not str(target).startswith(str(dest_root.resolve())):
                raise ValueError(f"Unsafe ZIP member rejected: {member.filename}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append(target)
    return extracted


def prepare_inputs(uploaded_paths: List[str], run_root: Path) -> Tuple[List[Path], List[Path]]:
    input_root = run_root / "input"
    input_root.mkdir(parents=True, exist_ok=True)
    all_files = []
    for raw in uploaded_paths:
        src = Path(raw)
        if src.suffix.lower() == ".zip":
            all_files.extend(safe_extract_zip(src, input_root / src.stem))
        else:
            dst = input_root / src.name
            shutil.copy2(src, dst)
            all_files.append(dst)

    raw_files, gt_files = [], []
    for path in all_files:
        low = str(path).lower().replace("\\", "/")
        if "ground_truth_eval_only" in low:
            if path.suffix.lower() in {".json", ".csv"}:
                gt_files.append(path)
        elif path.suffix.lower() in ALLOWED_SUFFIXES - {".zip"}:
            if "raw_logs" in low or path.suffix.lower() in {".jsonl", ".log", ".txt"}:
                raw_files.append(path)
    return sorted(raw_files), sorted(gt_files)


def parse_timestamp(value: Any) -> Optional[str]:
    if value in (None, "", "null"):
        return None
    try:
        return dtparser.parse(str(value)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except Exception:
        return None


def parse_log_line(line: str, source_file: str, line_no: int) -> LogEvent:
    raw = line.rstrip("\n")
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            msg = obj.get("message") or obj.get("msg") or obj.get("log") or obj.get("event") or raw
            return LogEvent(
                source_file=source_file,
                line_no=line_no,
                timestamp=parse_timestamp(obj.get("ts") or obj.get("timestamp") or obj.get("time") or obj.get("@timestamp")),
                level=str(obj.get("level") or obj.get("severity") or obj.get("log_level") or "UNKNOWN").upper(),
                service=str(obj.get("service") or obj.get("app") or obj.get("logger") or obj.get("component") or obj.get("pod") or "unknown"),
                message=str(msg),
                trace_id=obj.get("trace_id") or obj.get("traceId") or obj.get("correlation_id") or obj.get("request_id"),
                span_id=obj.get("span_id") or obj.get("spanId"),
                host=obj.get("host"),
                namespace=obj.get("namespace"),
                pod=obj.get("pod"),
                container=obj.get("container"),
                raw_line=raw,
                metadata={k: v for k, v in obj.items() if k not in {"message", "msg", "log"}},
            )
    except Exception:
        pass

    ts = None
    m_ts = re.search(r"(20\d{2}-\d{2}-\d{2}[T ][0-9:.+-]+Z?)", raw)
    if m_ts:
        ts = parse_timestamp(m_ts.group(1))
    m_level = re.search(r"\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b", raw, re.I)
    level = (m_level.group(1).upper() if m_level else "UNKNOWN").replace("WARNING", "WARN")
    m_service = re.search(r"(?:service|app|component|pod)=([A-Za-z0-9_.-]+)", raw)
    service = m_service.group(1) if m_service else "unknown"
    return LogEvent(source_file=source_file, line_no=line_no, timestamp=ts, level=level, service=service, message=raw, raw_line=raw, parse_status="text")


def parse_raw_files(raw_files: List[Path], run_root: Path) -> List[LogEvent]:
    events = []
    input_root = (run_root / "input").resolve()
    for file_path in raw_files:
        try:
            rel = str(file_path.resolve().relative_to(input_root))
        except Exception:
            rel = file_path.name
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                for line_no, line in enumerate(fh, start=1):
                    if line.strip():
                        events.append(parse_log_line(line, rel, line_no))
        except Exception as exc:
            events.append(LogEvent(source_file=rel, line_no=0, message=f"FAILED_TO_READ: {exc}", raw_line="", parse_status="error"))
    return events


SIGNAL_RULES = [
    ("Database", "db_hikari_timeout", "hikari_timeout", 4.5, "P1", r"hikaripool|connection pool|sqltransientconnection|too many clients|remaining connection slots|pg_stat_activity"),
    ("Database", "db_lock_slow_query", "db_lock_or_slow_query", 3.5, "P2", r"lock wait|deadlock|slow query|sequential scan|work_mem|jdbc connection"),
    ("Network", "network_connectivity", "network_connectivity", 3.0, "P2", r"dns failure|connection reset|connection refused|tls handshake|tcp retransmit|network unreachable|no route to host"),
    ("Authentication", "auth_jwt_rbac", "auth_token_or_rbac", 3.0, "P2", r"jwt|invalid token|invalid signature|issuer mismatch|jwk|401|403|rbac|unauthorized|forbidden|audience claim"),
    ("Memory/CPU", "resource_pressure", "resource_pressure", 4.0, "P1", r"oomkilled|out of memory|heap|gc pause|cpu thrott|restart loop|memory pressure|evicted|back-off restarting"),
    ("Deployment regression", "deployment_regression", "deployment_regression", 4.0, "P1", r"rollout started|deployment failed|deployment regression|canary failed|rollback recommended|feature flag enabled|configmap changed|new version only|error_budget_burn"),
    ("API timeout", "api_timeout", "api_timeout", 3.0, "P2", r"\b504\b|gateway timeout|upstream timed out|request timeout|p95|latency breach|circuit breaker|read timed out"),
    ("Queue backlog", "queue_backlog", "queue_backlog", 3.0, "P2", r"consumer lag|dlq|dead letter|retry topic|poison message|rebalance|queue backlog|kafka lag"),
    ("Disk/storage", "disk_storage", "disk_or_storage", 4.0, "P1", r"no space left|disk pressure|logrotate failed|io wait|persistent volume|volume full|storage latency|disk full|ephemeral-storage"),
    ("External dependency", "external_dependency", "external_dependency", 3.0, "P2", r"vendor|provider 5xx|http 429|retry-after|feed delayed|external dependency|third-party|rate limited|too many requests"),
    ("Unknown", "unknown_incomplete_trace", "unknown_incomplete_trace", 1.0, "P3", r"missing correlation|incomplete trace|unexpected state|redacted stack|insufficient evidence"),
]
COMPILED_RULES = [(cat, rid, sig, w, sev, re.compile(pat, re.I)) for cat, rid, sig, w, sev, pat in SIGNAL_RULES]


def extract_signals(events: List[LogEvent]) -> List[SignalMatch]:
    signals = []
    for ev in events:
        hay = f"{ev.level} {ev.service} {ev.message}"
        for category, rule_id, signature, weight, sev, regex in COMPILED_RULES:
            if regex.search(hay):
                signals.append(
                    SignalMatch(
                        signal_type=category,
                        rule_id=rule_id,
                        signature=signature,
                        weight=weight,
                        severity_hint=sev,
                        source_file=ev.source_file,
                        line_no=ev.line_no,
                        timestamp=ev.timestamp,
                        service=ev.service,
                        level=ev.level,
                        message=ev.message[:800],
                        trace_id=ev.trace_id,
                    )
                )
    return signals


def strongest_severity(severities: Iterable[str]) -> str:
    vals = [s if s in SEVERITY_ORDER else "UNKNOWN" for s in severities]
    return min(vals or ["UNKNOWN"], key=lambda x: SEVERITY_ORDER[x])


def build_evidence_clusters(signals: List[SignalMatch], options: Dict[str, Any]) -> List[EvidenceCluster]:
    grouped: Dict[Tuple[str, str, str], List[SignalMatch]] = defaultdict(list)
    for sig in signals:
        source_bucket = Path(sig.source_file).name
        grouped[(sig.signal_type, source_bucket, sig.signature)].append(sig)

    max_evidence = int(options.get("max_evidence_per_cluster", 25))
    clusters = []
    for (category, source_bucket, signature), items in grouped.items():
        items = sorted(items, key=lambda x: (x.timestamp or "", x.source_file, x.line_no))
        total_weight = sum(i.weight for i in items)
        if total_weight < 2.0 and category != "Unknown":
            continue
        sev = strongest_severity(i.severity_hint for i in items)
        services = sorted({i.service for i in items if i.service}) or [source_bucket]
        traces = sorted({str(i.trace_id) for i in items if i.trace_id})[:20]
        evidence = [model_to_dict(i) for i in items[:max_evidence]]
        raw_key = f"{category}|{source_bucket}|{signature}|{items[0].source_file}|{items[0].line_no}"
        cluster_id = "cluster_" + hashlib.sha1(raw_key.encode()).hexdigest()[:10]
        clusters.append(
            EvidenceCluster(
                cluster_id=cluster_id,
                candidate_category=category,
                signature=signature,
                affected_services=services,
                start_ts=items[0].timestamp,
                end_ts=items[-1].timestamp,
                window="all-window",
                signal_count=len(items),
                total_weight=round(total_weight, 2),
                severity_hint=sev,
                evidence=evidence,
                rule_ids=sorted({i.rule_id for i in items}),
                trace_ids=traces,
                summary=f"{category} signals for {', '.join(services[:4])}; signature={signature}; evidence={len(items)}.",
            )
        )
    clusters.sort(key=lambda c: (SEVERITY_ORDER.get(c.severity_hint, 5), -c.total_weight, c.candidate_category))
    return clusters[: int(options.get("max_clusters", 25) or 25)]


EMBEDDED_RUNBOOKS = [
    {
        "title": "Database connection pool exhaustion",
        "incident_type": "Database",
        "symptoms": ["HikariPool", "too many clients", "JDBC timeout", "remaining connection slots"],
        "diagnostics": ["Check pg_stat_activity and connection counts", "Inspect lock waits and long-running transactions", "Review DB pool acquisition latency"],
        "remediation": ["Reduce request pressure or shed non-critical traffic", "Tune pool size only after DB capacity review", "Terminate idle-in-transaction sessions only after approval"],
        "validation": ["DB wait time returns to baseline", "5xx rate drops", "Pool acquisition latency normalizes"],
        "safety_notes": ["Do not restart DB primary blindly", "Do not increase pools without DB capacity check"],
        "owner": "sre",
        "source": "embedded_runbook",
    },
    {
        "title": "Authentication token validation failure",
        "incident_type": "Authentication",
        "symptoms": ["JWT", "issuer mismatch", "invalid signature", "JWK", "401", "403"],
        "diagnostics": ["Verify issuer and audience configuration", "Check JWK refresh and key rotation", "Compare failed token kid values"],
        "remediation": ["Rollback incorrect auth config", "Refresh JWK cache", "Coordinate key rotation rollback if needed"],
        "validation": ["401/403 spike returns to baseline", "Token validation succeeds for known-good users"],
        "safety_notes": ["Do not disable auth validation", "Human approval required before broad RBAC changes"],
        "owner": "identity-platform",
        "source": "embedded_runbook",
    },
    {
        "title": "API timeout and downstream latency",
        "incident_type": "API timeout",
        "symptoms": ["504", "upstream timed out", "p95", "circuit breaker"],
        "diagnostics": ["Identify slow downstream service", "Check gateway and upstream timeout settings", "Inspect dependency health"],
        "remediation": ["Throttle or degrade non-critical paths", "Increase timeout only with downstream owner agreement", "Roll back recent latency-causing change"],
        "validation": ["p95 latency normalizes", "504 rate decreases", "Circuit breaker closes"],
        "safety_notes": ["Do not mask true outage by only increasing timeouts"],
        "owner": "platform",
        "source": "embedded_runbook",
    },
    {
        "title": "Memory or CPU saturation",
        "incident_type": "Memory/CPU",
        "symptoms": ["OOMKilled", "heap", "GC pause", "CPU throttling", "restart loop"],
        "diagnostics": ["Check pod restarts and resource limits", "Inspect heap/GC and CPU throttling metrics", "Compare recent traffic or deployment changes"],
        "remediation": ["Scale replicas if downstream capacity allows", "Rollback leak-inducing release", "Tune memory limits after profiling"],
        "validation": ["Restart rate falls", "GC pauses normalize", "CPU throttling drops"],
        "safety_notes": ["Avoid blind restarts without preserving diagnostics"],
        "owner": "service-owner",
        "source": "embedded_runbook",
    },
    {
        "title": "Deployment regression",
        "incident_type": "Deployment regression",
        "symptoms": ["rollout", "canary", "feature flag", "configmap", "rollback"],
        "diagnostics": ["Compare errors before and after rollout", "Check canary metrics and feature flag changes", "Review config diffs"],
        "remediation": ["Rollback bad version or disable feature flag", "Freeze further rollout", "Notify owning team"],
        "validation": ["Errors drop after rollback", "Canary health returns to green"],
        "safety_notes": ["Confirm correlation before declaring causation"],
        "owner": "release-manager",
        "source": "embedded_runbook",
    },
    {
        "title": "Queue backlog",
        "incident_type": "Queue backlog",
        "symptoms": ["consumer lag", "DLQ", "poison message", "rebalance"],
        "diagnostics": ["Check consumer lag by partition", "Inspect DLQ messages", "Identify poison-message pattern"],
        "remediation": ["Pause bad producer or quarantine poison messages", "Scale consumers if safe", "Replay DLQ after fix"],
        "validation": ["Lag decreases", "DLQ growth stops"],
        "safety_notes": ["Avoid replaying poison messages before fix"],
        "owner": "data-platform",
        "source": "embedded_runbook",
    },
    {
        "title": "Disk or storage pressure",
        "incident_type": "Disk/storage",
        "symptoms": ["no space left", "disk pressure", "logrotate", "io wait", "volume full"],
        "diagnostics": ["Check filesystem usage and inode pressure", "Find largest directories", "Inspect storage backend latency"],
        "remediation": ["Clean safe temporary/log files", "Expand volume with approval", "Fix logrotate"],
        "validation": ["Disk usage below threshold", "IO wait returns to baseline"],
        "safety_notes": ["Do not delete application data without owner approval"],
        "owner": "infra",
        "source": "embedded_runbook",
    },
    {
        "title": "External dependency degradation",
        "incident_type": "External dependency",
        "symptoms": ["vendor", "provider 5xx", "429", "Retry-After", "feed delayed"],
        "diagnostics": ["Check provider status page", "Inspect retry-after and throttling headers", "Compare across regions"],
        "remediation": ["Enable graceful degradation", "Back off retries", "Escalate to vendor"],
        "validation": ["Vendor error rate falls", "Retry queue drains"],
        "safety_notes": ["Avoid retry storms that amplify provider outage"],
        "owner": "vendor-management",
        "source": "embedded_runbook",
    },
    {
        "title": "Unknown incident triage",
        "incident_type": "Unknown",
        "symptoms": ["missing correlation", "incomplete trace", "redacted stack", "unexpected state"],
        "diagnostics": ["Collect missing traces", "Increase safe logging around failing path", "Ask service owner for recent changes"],
        "remediation": ["Open investigation ticket", "Preserve evidence", "Do not execute disruptive remediation without evidence"],
        "validation": ["Additional telemetry collected", "Hypothesis updated with evidence"],
        "safety_notes": ["Declare uncertainty clearly"],
        "owner": "sre",
        "source": "embedded_runbook",
    },
]


def lexical_score(cluster: EvidenceCluster, rb: Dict[str, Any]) -> float:
    blob = " ".join([cluster.candidate_category, cluster.signature, cluster.summary] + [e.get("message", "") for e in cluster.evidence[:10]]).lower()
    terms = [rb.get("incident_type", ""), rb.get("title", "")] + rb.get("symptoms", [])
    return sum(1.0 for term in terms if str(term).lower() in blob)


def retrieve_runbook_context(clusters: List[EvidenceCluster], options: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    if not options.get("enable_rag", True):
        return {c.cluster_id: [] for c in clusters}
    try:
        from src.rag import retrieve_rag_context

        external = retrieve_rag_context({"clusters": [model_to_dict(c) for c in clusters]})
        if external:
            return external
    except Exception as exc:
        print(f"[RAG] Local RAG unavailable, using embedded runbooks. Reason: {exc}")

    result = {}
    for cluster in clusters:
        scored = []
        for rb in EMBEDDED_RUNBOOKS:
            score = lexical_score(cluster, rb)
            if rb["incident_type"] == cluster.candidate_category:
                score += 3.0
            if score > 0:
                enriched = dict(rb)
                enriched["score"] = round(score, 2)
                scored.append(enriched)
        scored.sort(key=lambda item: -item["score"])
        result[cluster.cluster_id] = scored[:3]
    return result


def evidence_ref(evidence: Dict[str, Any]) -> str:
    return f"{evidence.get('source_file')}:{evidence.get('line_no')} - {str(evidence.get('message', ''))[:240]}"


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


def timeline_agent(cluster: EvidenceCluster) -> Dict[str, Any]:
    events = []
    for e in cluster.evidence[:12]:
        events.append(
            {
                "timestamp": e.get("timestamp"),
                "source_file": e.get("source_file"),
                "line_no": e.get("line_no"),
                "service": e.get("service"),
                "level": e.get("level"),
                "message": e.get("message"),
            }
        )
    interpretation = f"Signals start at {cluster.start_ts or 'unknown'} and end at {cluster.end_ts or 'unknown'} for {', '.join(cluster.affected_services[:4])}."
    return {"events": events, "interpretation": interpretation}


def symptom_cause_text(category: str) -> str:
    mapping = {
        "Database": "Database signals are the primary hypothesis; API timeout lines may be downstream symptoms.",
        "API timeout": "API timeout may be a symptom; confirm downstream dependency latency before treating gateway timeout as root cause.",
        "Deployment regression": "Deployment correlation is strong but should be confirmed against error onset and rollback behavior.",
        "External dependency": "Third-party/provider failures are likely external causes; internal retries may amplify symptoms.",
        "Unknown": "Evidence is insufficient; treat this as investigation-first rather than remediation-first.",
    }
    return mapping.get(category, f"{category} evidence is the primary hypothesis; validate with service metrics and recent changes.")


def rca_agent(cluster: EvidenceCluster, classification: Dict[str, Any], timeline: Dict[str, Any], rag_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    refs = [evidence_ref(e) for e in cluster.evidence[:10]]
    primary_by_cat = {
        "Database": "Likely database connection pool exhaustion, lock contention, or slow query pressure.",
        "Network": "Likely upstream connectivity, DNS, TLS, or network path instability.",
        "Authentication": "Likely token validation, JWK/key rotation, issuer/audience, or RBAC configuration issue.",
        "Memory/CPU": "Likely resource saturation, OOM, memory leak, CPU throttling, or GC pause.",
        "Deployment regression": "Likely bad release, feature flag, or configuration regression.",
        "API timeout": "Likely downstream latency cascade or gateway/upstream timeout failure.",
        "Queue backlog": "Likely slow consumers, poison message, retry storm, or rebalance instability.",
        "Disk/storage": "Likely disk exhaustion, log growth, or storage backend latency.",
        "External dependency": "Likely third-party degradation, throttling, or provider outage.",
        "Unknown": "Insufficient evidence to identify a single root cause.",
    }
    rag_sources = [f"{c.get('title')} ({c.get('source')})" for c in rag_chunks[:3] if c.get("source")]
    return {
        "primary_root_cause": primary_by_cat.get(classification["category"], "Likely operational incident requiring investigation."),
        "alternative_causes": ["recent deployment/config change", "upstream dependency degradation", "traffic spike or retry amplification"],
        "supporting_evidence": refs,
        "rag_sources": rag_sources,
        "missing_evidence": ["service metrics", "recent deployment history", "distributed traces", "owner confirmation"],
        "confidence": classification["confidence"],
    }


def remediation_agent(cluster: EvidenceCluster, rca: Dict[str, Any], rag_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    actions, validation, safety = [], [], []
    for rb in rag_chunks[:2]:
        actions.extend(rb.get("diagnostics", []) + rb.get("remediation", []))
        validation.extend(rb.get("validation", []))
        safety.extend(rb.get("safety_notes", []))
        if not rb.get("diagnostics") and rb.get("content"):
            actions.append(str(rb["content"])[:500])
    if not actions:
        actions = ["Preserve evidence", "Collect service metrics and traces", "Open owner investigation ticket"]
    safety.append("Human approval required before disruptive remediation or external notification.")
    return {
        "immediate_actions": list(dict.fromkeys(actions))[:10],
        "validation_checks": list(dict.fromkeys(validation or ["error rate returns to baseline", "customer impact stops"]))[:8],
        "safety_notes": list(dict.fromkeys(safety))[:8],
        "requires_human_approval": True,
    }


def critic_agent(cluster: EvidenceCluster, incident: Dict[str, Any]) -> Tuple[List[str], bool]:
    findings = []
    grounded = bool(cluster.evidence) and bool(incident.get("root_cause", {}).get("supporting_evidence"))
    findings.append("Evidence grounding passed." if grounded else "Evidence grounding weak: no cited log lines.")
    if incident.get("remediation", {}).get("requires_human_approval"):
        findings.append("Safety gate present: preview only until human approval.")
    else:
        findings.append("Safety issue: missing human approval gate.")
    if incident.get("category") == "Unknown":
        findings.append("Uncertainty is explicit; recommends more telemetry instead of disruptive action.")
    return findings, grounded


def build_action_payload(run_id: str, incident: IncidentResult, approval_status: str = "PREVIEW_ONLY") -> ActionPayload:
    evidence = incident.root_cause.get("supporting_evidence", [])
    actions = incident.remediation.get("immediate_actions", [])
    safety = incident.remediation.get("safety_notes", [])
    labels = ["ai-generated", "incident", incident.severity.lower(), incident.category.lower().replace("/", "-").replace(" ", "-")]
    ticket = TicketPayload(
        title=f"{incident.severity}: {incident.category} - {incident.title}",
        priority=incident.severity,
        labels=labels,
        description=(
            f"Root cause: {incident.root_cause.get('primary_root_cause')}\n\nEvidence:\n- "
            + "\n- ".join(evidence[:10])
            + "\n\nRecommended actions:\n- "
            + "\n- ".join(actions[:10])
            + "\n\nSafety notes:\n- "
            + "\n- ".join(safety[:10])
        ),
        evidence=evidence,
        approval_status=approval_status,
    )
    slack = SlackPayload(
        title=f"{incident.severity}: {incident.category} incident candidate",
        body=(
            f"Affected services: {', '.join(incident.affected_services)}\n"
            f"Likely cause: {incident.root_cause.get('primary_root_cause')}\n"
            f"Top evidence: {(evidence[0] if evidence else 'n/a')}\n"
            f"Top action: {(actions[0] if actions else 'n/a')}\n"
            f"Status: {approval_status}; human approval required."
        ),
        approval_status=approval_status,
    )
    cookbook = CookbookPayload(title=f"Cookbook: {incident.category} / {incident.cluster_id}", steps=actions, validation=incident.remediation.get("validation_checks", []), safety_notes=safety)
    return ActionPayload(run_id=run_id, approval_status=approval_status, incident_id=incident.incident_id, severity=incident.severity, category=incident.category, ticket=ticket, slack=slack, cookbook=cookbook)


def run_incident_agents(run_id: str, clusters: List[EvidenceCluster], rag_context: Dict[str, List[Dict[str, Any]]]) -> Tuple[List[IncidentResult], List[ActionPayload]]:
    incidents, actions = [], []
    for cluster in clusters:
        rag_chunks = rag_context.get(cluster.cluster_id, [])
        classification = classifier_agent(cluster, rag_chunks)
        timeline = timeline_agent(cluster)
        rca = rca_agent(cluster, classification, timeline, rag_chunks)
        remediation = remediation_agent(cluster, rca, rag_chunks)
        draft = {"category": classification["category"], "severity": classification["severity"], "root_cause": rca, "remediation": remediation}
        findings, grounded = critic_agent(cluster, draft)
        incident = IncidentResult(
            incident_id=cluster.cluster_id,
            cluster_id=cluster.cluster_id,
            category=classification["category"],
            severity=classification["severity"],
            confidence=classification["confidence"],
            title=classification["title"],
            affected_services=cluster.affected_services,
            symptom_vs_cause=symptom_cause_text(classification["category"]),
            timeline=timeline,
            root_cause=rca,
            remediation=remediation,
            critic_findings=findings,
            evidence_grounded=grounded,
            approval_status="PENDING_HUMAN_APPROVAL",
        )
        incidents.append(incident)
        actions.append(build_action_payload(run_id, incident))
    return incidents, actions


def load_ground_truth(gt_files: List[Path]) -> List[Dict[str, Any]]:
    cases = []
    for path in gt_files:
        try:
            if path.name == "golden_labels.json":
                data = json.loads(path.read_text(encoding="utf-8"))
                cases.extend(data if isinstance(data, list) else data.get("cases", []))
            elif path.name.endswith(".csv"):
                with open(path, newline="", encoding="utf-8") as fh:
                    for row in csv.DictReader(fh):
                        cases.append(row)
        except Exception as exc:
            cases.append({"_load_error": str(exc), "file": str(path)})
    seen, out = set(), []
    for case in cases:
        key = (case.get("case_id"), case.get("raw_file"), case.get("expected_category"))
        if key not in seen and case.get("expected_category"):
            seen.add(key)
            out.append(case)
    return out


def score_evals(incidents: List[IncidentResult], gt_files: List[Path]) -> Dict[str, Any]:
    cases = load_ground_truth(gt_files)
    if not cases:
        return {"enabled": False, "summary": None, "note": "No ground_truth_eval_only files found."}
    inc_dicts = [model_to_dict(i) for i in incidents]
    details = []
    cat_hits = sev_hits = ticket_hits = evidence_hits = 0
    for case in cases:
        expected_cat = case.get("expected_category")
        expected_sev = case.get("expected_severity") or "UNKNOWN"
        raw_file = str(case.get("raw_file") or "").split("/")[-1]
        matched = []
        for inc in inc_dicts:
            evidence = "\n".join(inc.get("root_cause", {}).get("supporting_evidence", []))
            if inc.get("category") == expected_cat and ((not raw_file) or raw_file in evidence):
                matched.append(inc)
        cat_ok = bool(matched)
        sev_ok = any(m.get("severity") == expected_sev for m in matched)
        ticket_expected = str(case.get("expected_behavior", {})).lower().find("create_ticket") >= 0 or expected_sev in {"P1", "P2"}
        ticket_ok = any(m.get("severity") in {"P1", "P2"} for m in matched) if ticket_expected else True
        terms = case.get("expected_evidence_terms") or []
        term_ok = True
        if isinstance(terms, list) and terms:
            combined = "\n".join(["\n".join(m.get("root_cause", {}).get("supporting_evidence", [])) for m in matched]).lower()
            term_ok = any(all(str(tok).lower() in combined for tok in group[:3]) for group in terms if isinstance(group, list)) if combined else False
        cat_hits += int(cat_ok)
        sev_hits += int(sev_ok)
        ticket_hits += int(ticket_ok)
        evidence_hits += int(term_ok and cat_ok)
        details.append({"case_id": case.get("case_id"), "raw_file": case.get("raw_file"), "expected_category": expected_cat, "expected_severity": expected_sev, "category_hit": cat_ok, "severity_hit": sev_ok, "ticket_hit": ticket_ok, "evidence_hit": bool(term_ok and cat_ok)})
    n = max(len(cases), 1)
    return {
        "enabled": True,
        "summary": {
            "cases": len(cases),
            "category_recall": round(cat_hits / n, 3),
            "severity_accuracy": round(sev_hits / n, 3),
            "ticket_trigger_accuracy": round(ticket_hits / n, 3),
            "evidence_grounding": round(evidence_hits / n, 3),
        },
        "details": details,
    }


def export_results(output_root: Path, state: GraphState) -> Dict[str, str]:
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / "analysis_response.json"
    md_path = output_root / "incident_report.md"
    csv_path = output_root / "incidents.csv"
    clusters_path = output_root / "evidence_clusters.csv"
    zip_path = output_root.parent / f"{state.run_id}_outputs.zip"

    payload = {
        "run_id": state.run_id,
        "summary": {
            "raw_files": len(state.raw_files),
            "events_parsed": len(state.events),
            "signals_found": len(state.signals),
            "clusters_found": len(state.clusters),
            "incidents_found": len(state.incidents),
            "ground_truth_files_detected_but_not_used_by_runtime": len(state.ground_truth_files),
            "errors": state.errors,
        },
        "clusters": [model_to_dict(c) for c in state.clusters],
        "rag_context": state.rag_context,
        "incidents": [model_to_dict(i) for i in state.incidents],
        "action_payloads": [model_to_dict(a) for a in state.action_payloads],
        "eval": state.eval_summary,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [f"# IncidentIQ Analysis Report - {state.run_id}", "", "## Summary"]
    for key, value in payload["summary"].items():
        lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
    if state.eval_summary:
        lines += ["", "## Evaluation Summary", "```json", json.dumps(state.eval_summary.get("summary"), indent=2), "```"]
    lines.append("\n## Incidents")
    for inc in state.incidents:
        lines += [
            f"\n### {inc.title}",
            f"- Category: **{inc.category}**",
            f"- Severity: **{inc.severity}**",
            f"- Confidence: {inc.confidence}",
            f"- Affected services: {', '.join(inc.affected_services)}",
            f"- Symptom vs cause: {inc.symptom_vs_cause}",
            f"- RCA: {inc.root_cause.get('primary_root_cause')}",
            "- Evidence:",
        ]
        lines += [f"  - {e}" for e in inc.root_cause.get("supporting_evidence", [])[:8]]
        if inc.root_cause.get("rag_sources"):
            lines += ["- RAG sources:"] + [f"  - {src}" for src in inc.root_cause.get("rag_sources", [])[:5]]
        lines += ["- Immediate actions:"] + [f"  - {a}" for a in inc.remediation.get("immediate_actions", [])[:8]]
        lines += ["- Safety notes:"] + [f"  - {s}" for s in inc.remediation.get("safety_notes", [])[:6]]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    pd.DataFrame(
        [
            {
                "incident_id": i.incident_id,
                "category": i.category,
                "severity": i.severity,
                "confidence": i.confidence,
                "affected_services": "|".join(i.affected_services),
                "title": i.title,
                "primary_root_cause": i.root_cause.get("primary_root_cause"),
                "approval_status": i.approval_status,
            }
            for i in state.incidents
        ]
    ).to_csv(csv_path, index=False)
    pd.DataFrame(
        [
            {
                "cluster_id": c.cluster_id,
                "category": c.candidate_category,
                "severity_hint": c.severity_hint,
                "services": "|".join(c.affected_services),
                "signals": c.signal_count,
                "weight": c.total_weight,
                "signature": c.signature,
                "window": c.window,
            }
            for c in state.clusters
        ]
    ).to_csv(clusters_path, index=False)

    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in [json_path, md_path, csv_path, clusters_path]:
            zf.write(path, arcname=path.name)
    return {"markdown": str(md_path), "json": str(json_path), "csv": str(csv_path), "clusters_csv": str(clusters_path), "output_zip": str(zip_path)}


def run_analysis(request: AnalysisRequest) -> AnalysisResponse:
    options = {**DEFAULT_OPTIONS, **(request.options or {})}
    run_root = WORK_ROOT / "runs" / request.run_id
    output_root = run_root / "outputs"
    run_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)
    state = GraphState(run_id=request.run_id, input_paths=request.uploaded_paths, runtime_root=str(run_root))
    try:
        raw_files, gt_files = prepare_inputs(request.uploaded_paths, run_root)
        state.raw_files = [str(path) for path in raw_files]
        state.ground_truth_files = [str(path) for path in gt_files]
        state.events = parse_raw_files(raw_files, run_root)
        state.signals = extract_signals(state.events)
        state.clusters = build_evidence_clusters(state.signals, options)
        state.rag_context = retrieve_runbook_context(state.clusters, options)
        state.incidents, state.action_payloads = run_incident_agents(state.run_id, state.clusters, state.rag_context)
        state.eval_summary = score_evals(state.incidents, gt_files) if options.get("run_evals", True) else {"enabled": False, "summary": None, "note": "Eval disabled by options."}
        state.exports = export_results(output_root, state)
        status = "completed"
    except Exception as exc:
        state.errors.append(str(exc))
        state.exports = export_results(output_root, state)
        status = "failed"

    highest = strongest_severity([incident.severity for incident in state.incidents])
    return AnalysisResponse(
        run_id=state.run_id,
        status=status,
        highest_severity=highest,
        summary={
            "raw_files": len(state.raw_files),
            "events_parsed": len(state.events),
            "signals_found": len(state.signals),
            "clusters_found": len(state.clusters),
            "incidents_found": len(state.incidents),
            "ground_truth_files_detected_but_not_used_by_runtime": len(state.ground_truth_files),
            "errors": state.errors,
        },
        incidents=state.incidents,
        slack_payloads=[action.slack for action in state.action_payloads],
        jira_payloads=[action.ticket for action in state.action_payloads],
        cookbooks=[action.cookbook for action in state.action_payloads],
        reports=state.exports,
        eval=state.eval_summary or {},
        errors=state.errors,
    )


def analyze_uploaded_logs(files_or_paths: Iterable[Any], options: Optional[Dict[str, Any]] = None) -> AnalysisResponse:
    run_id = new_run_id()
    saved = safe_copy_uploads(files_or_paths, run_id)
    request = AnalysisRequest(run_id=run_id, uploaded_paths=saved, options={**DEFAULT_OPTIONS, **(options or {})})
    return run_analysis(request)


def response_to_markdown(response: AnalysisResponse) -> str:
    lines = [
        "# IncidentIQ Result",
        "",
        f"**Run:** `{response.run_id}`",
        f"**Status:** {response.status}",
        f"**Highest severity:** {response.highest_severity}",
        "",
        "## Summary",
    ]
    for key, value in response.summary.items():
        lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
    if response.eval and response.eval.get("summary"):
        lines += ["", "## Eval", "```json", json.dumps(response.eval.get("summary"), indent=2), "```"]
    lines.append("\n## Top Incidents")
    for inc in response.incidents[:10]:
        lines += [
            f"\n### {inc.severity} - {inc.category}",
            f"**Title:** {inc.title}",
            f"**Affected services:** {', '.join(inc.affected_services)}",
            f"**RCA:** {inc.root_cause.get('primary_root_cause')}",
            f"**Top action:** {(inc.remediation.get('immediate_actions') or ['n/a'])[0]}",
            f"**Safety:** {(inc.remediation.get('safety_notes') or ['n/a'])[0]}",
        ]
        if inc.root_cause.get("supporting_evidence"):
            lines.append(f"**Evidence:** `{inc.root_cause['supporting_evidence'][0]}`")
        if inc.root_cause.get("rag_sources"):
            lines.append(f"**RAG source:** `{inc.root_cause['rag_sources'][0]}`")
    if not response.incidents:
        lines.append("No incident candidates found. Try a larger log sample or verify file format.")
    return "\n".join(lines)
