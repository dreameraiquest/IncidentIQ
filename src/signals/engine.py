import re
from typing import List
from src.models.log_event import LogEvent
from src.models.incident import SignalMatch

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
