import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv


load_dotenv()

RAG_ROOT = Path(__file__).resolve().parent
REPO_ROOT = RAG_ROOT.parents[1]
RAG_WORK_DIR = Path(os.getenv("workDir", str(RAG_ROOT)))
KNOWLEDGE_BASE = RAG_WORK_DIR / "knowledge_base"
FAISS_INDEX_PATH = RAG_WORK_DIR / "faiss_index"

TOP_K = int(os.getenv("INCIDENTIQ_RAG_TOP_K", "5"))


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9_/.-]+", text.lower()) if len(token) > 2}


def _read_docs(knowledge_base_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    kb_dir = Path(knowledge_base_dir or KNOWLEDGE_BASE)
    docs = []
    if not kb_dir.exists():
        return docs
    for path in sorted(kb_dir.rglob("*")):
        if path.suffix.lower() not in {".txt", ".md"} or not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        docs.append(
            {
                "title": _title_from_content(path, content),
                "source": str(path),
                "content": content,
                "incident_type": _field_from_content(content, "Category") or _infer_category(content),
                **_extract_sections(content),
            }
        )
    return docs


def _title_from_content(path: Path, content: str) -> str:
    for line in content.splitlines():
        stripped = line.strip("# ").strip()
        if stripped:
            return stripped[:120]
    return path.name


def _field_from_content(content: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}:\s*(.+)$", content, re.I | re.M)
    if not match:
        return ""
    return match.group(1).split("|")[0].strip()


def _infer_category(content: str) -> str:
    low = content.lower()
    mapping = {
        "Database": ["hikari", "postgres", "connection pool", "jdbc"],
        "Authentication": ["jwt", "issuer", "jwk", "rbac", "token"],
        "Queue backlog": ["kafka", "consumer lag", "dlq", "poison message"],
        "Disk/storage": ["disk", "storage", "logrotate", "no space"],
        "Deployment regression": ["deployment", "canary", "rollback", "feature flag"],
        "API timeout": ["504", "timeout", "gateway", "latency"],
        "Memory/CPU": ["oom", "memory", "cpu", "heap", "gc"],
        "External dependency": ["vendor", "provider", "429", "rate limit"],
        "Network": ["dns", "tls", "network", "connection reset"],
    }
    for category, terms in mapping.items():
        if any(term in low for term in terms):
            return category
    return "Unknown"


def _extract_sections(content: str) -> Dict[str, List[str]]:
    sections = {
        "diagnostics": [],
        "remediation": [],
        "validation": [],
        "safety_notes": [],
        "symptoms": [],
    }
    current = None
    aliases = {
        "diagnostics": "diagnostics",
        "diagnosis": "diagnostics",
        "triage": "diagnostics",
        "checks": "diagnostics",
        "remediation": "remediation",
        "actions": "remediation",
        "resolution": "remediation",
        "fix": "remediation",
        "validation": "validation",
        "verify": "validation",
        "verification": "validation",
        "safety": "safety_notes",
        "safety notes": "safety_notes",
        "symptoms": "symptoms",
    }
    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        heading = line.strip(":").lower()
        if heading in aliases:
            current = aliases[heading]
            continue
        if line.endswith(":") and line[:-1].strip().lower() in aliases:
            current = aliases[line[:-1].strip().lower()]
            continue
        if current and (line.startswith("-") or line[0:2].isdigit()):
            item = re.sub(r"^[-*\d.\s]+", "", line).strip()
            if item:
                sections[current].append(item)
    return sections


def _build_query(cluster: Dict[str, Any]) -> str:
    evidence_text = " ".join(e.get("message", "") for e in cluster.get("evidence", [])[:6] if e.get("message"))
    return " ".join(
        [
            cluster.get("candidate_category", ""),
            cluster.get("signature", ""),
            " ".join(cluster.get("affected_services", [])),
            evidence_text,
        ]
    )


def _score_doc(query_tokens: set[str], cluster: Dict[str, Any], doc: Dict[str, Any]) -> float:
    doc_tokens = _tokenize(" ".join([doc.get("title", ""), doc.get("incident_type", ""), doc.get("content", "")]))
    overlap = len(query_tokens & doc_tokens)
    score = float(overlap)
    if doc.get("incident_type") == cluster.get("candidate_category"):
        score += 8.0
    for service in cluster.get("affected_services", []):
        if service.lower() in doc.get("content", "").lower():
            score += 1.5
    return score


def retrieve_rag_context(analysis_context: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    docs = _read_docs()
    if not docs:
        return {}
    result: Dict[str, List[Dict[str, Any]]] = {}
    for cluster in analysis_context.get("clusters", []):
        cluster_id = cluster.get("cluster_id", "unknown")
        query_tokens = _tokenize(_build_query(cluster))
        scored = []
        for doc in docs:
            score = _score_doc(query_tokens, cluster, doc)
            if score <= 0:
                continue
            item = dict(doc)
            item["score"] = round(score, 3)
            scored.append(item)
        scored.sort(key=lambda item: -item["score"])
        result[cluster_id] = scored[:TOP_K]
    return result


def ingest(knowledge_base_dir: Optional[Path] = None, index_path: Optional[Path] = None) -> None:
    """Build a FAISS index when optional vector dependencies are installed.

    The runtime does not require this. If dependencies are unavailable, lexical
    retrieval from the same knowledge base remains the fallback path.
    """
    kb_dir = Path(knowledge_base_dir or KNOWLEDGE_BASE)
    idx_dir = Path(index_path or FAISS_INDEX_PATH)
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.document_loaders import TextLoader
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceEmbeddings
    except Exception as exc:
        raise RuntimeError(f"Optional FAISS dependencies are not installed: {exc}") from exc

    docs = []
    for path in sorted(kb_dir.rglob("*.txt")):
        loaded = TextLoader(str(path), encoding="utf-8").load()
        for doc in loaded:
            doc.metadata["source"] = str(path)
        docs.extend(loaded)
    if not docs:
        raise FileNotFoundError(f"No .txt documents found under {kb_dir}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    idx_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(idx_dir))


def dump_debug_context(path: str, analysis_context: Dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(retrieve_rag_context(analysis_context), indent=2), encoding="utf-8")
