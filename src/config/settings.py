import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

WORK_ROOT = Path(
    os.getenv(
        "INCIDENTIQ_WORK_ROOT",
        "/content/incidentiq_work" if Path("/content").exists() else "/tmp/incidentiq_work"
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
    "Database", "Network", "Authentication", "Memory/CPU", 
    "Deployment regression", "API timeout", "Queue backlog", 
    "Disk/storage", "External dependency", "Unknown"
]
SEVERITY_ORDER = {"P1": 1, "P2": 2, "P3": 3, "P4": 4, "UNKNOWN": 5}
