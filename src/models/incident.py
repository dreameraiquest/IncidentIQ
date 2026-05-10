from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

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
