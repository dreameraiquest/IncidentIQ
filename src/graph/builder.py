import os
import json
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from src.config.settings import WORK_ROOT, DEFAULT_OPTIONS, SEVERITY_ORDER, ALLOWED_SUFFIXES
from src.ingest.log_parser import parse_log_line
from src.signals.engine import extract_signals
from src.clustering.evidence_clusterer import build_evidence_clusters
from src.rag.retriever import retrieve_rag_context
from src.agents.classifier import classifier_agent
from src.agents.rca_remedy import rca_agent, remediation_agent
from src.agents.timeline_critic import timeline_agent, critic_agent
from src.integrations.n8n import send_incident_to_n8n
from src.reporting.markdown_report import response_to_markdown
from src.models.incident import IncidentResult

def analyze_uploaded_logs(file_paths: List[str], options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Main pipeline entry point aligned with the 8-Step Flow in the Detailed Guide.
    """
    opts = {**DEFAULT_OPTIONS, **(options or {})}
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir = WORK_ROOT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # --- STEP 1 & 2: Input & Ingest ---
    events = []
    for fp in file_paths:
        path = Path(fp)
        if path.suffix == ".zip":
            with zipfile.ZipFile(path, 'r') as z:
                for name in z.namelist():
                    if any(name.endswith(s) for s in ALLOWED_SUFFIXES):
                        with z.open(name) as f:
                            lines = f.read().decode('utf-8', errors='ignore').splitlines()
                            for i, line in enumerate(lines):
                                events.append(parse_log_line(line, name, i+1))
        elif path.suffix in ALLOWED_SUFFIXES:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    events.append(parse_log_line(line, path.name, i+1))

    # --- STEP 3: Signal Detection ---
    signals = extract_signals(events)
    
    # --- STEP 4: Clustering ---
    clusters = build_evidence_clusters(signals, opts, SEVERITY_ORDER)
    
    # --- STEP 5: Agent Reasoning (with RAG) ---
    incidents = []
    for cluster in clusters:
        # Step 5: Retrieve RAG Library Context
        rag_chunks = retrieve_rag_context(cluster.candidate_category, cluster.signature)
        
        # Collaborative Agent Reasoning
        c_res = classifier_agent(cluster, rag_chunks)
        r_res = rca_agent(cluster, rag_chunks)
        m_res = remediation_agent(cluster, rag_chunks)
        t_res = timeline_agent(cluster)
        
        # Build the final incident object
        inc_data = {
            "incident_id": cluster.cluster_id,
            "cluster_id": cluster.cluster_id,
            "category": c_res["category"],
            "severity": c_res["severity"],
            "confidence": c_res["confidence"],
            "title": c_res["title"],
            "affected_services": cluster.affected_services,
            "symptom_vs_cause": r_res["symptom_vs_cause"],
            "timeline": t_res,
            "root_cause": r_res,
            "remediation": m_res
        }
        
        # Critic Review
        inc_data["critic_findings"] = critic_agent(inc_data)
        
        # --- STEP 6: Reporting & n8n Integration ---
        if opts.get("enable_real_integrations"):
            send_incident_to_n8n(inc_data)
            
        incidents.append(IncidentResult(**inc_data))
    
    # --- STEP 7: Evaluation (Optional/Isolated) ---
    summary = {
        "run_id": run_id,
        "highest_severity": min((i.severity for i in incidents), key=lambda x: SEVERITY_ORDER.get(x, 5)) if incidents else "UNKNOWN",
        "signals_found": len(signals),
        "events_parsed": len(events),
        "incidents_found": len(incidents),
        "steps_completed": ["Ingest", "Signals", "Clustering", "Reasoning", "Reporting", "n8n"]
    }
    
    # --- STEP 8: Export Bundle ---
    report_md = response_to_markdown(incidents, summary)
    output_json = {
        "run_id": run_id,
        "status": "completed",
        "summary": summary,
        "incidents": [i.model_dump() for i in incidents]
    }
    
    with open(run_dir / "analysis_response.json", "w") as f:
        json.dump(output_json, f, indent=2)
    with open(run_dir / "report.md", "w") as f:
        f.write(report_md)

    return output_json
