# src/rag/rag_retriever.py
# ─────────────────────────────────────────────────────────────────────────────
# Drop-in RAG implementation for the IncidentIQ pipeline.
#
# This module is designed to be called by the notebook's retrieve_runbook_context
# It adds a real FAISS + LangChain + OpenAI retrieval system.
# with lexical RUNBOOKS as fallback
#
# ─────────────────────────────────────────────────────────────────────────────

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── LangChain imports ─────────────────────────────────────────────────────────
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# ─────────────────────────────────────────────────────────────────────────────
# Config — all paths relative to repo root so it works both locally and in Colab
# ─────────────────────────────────────────────────────────────────────────────
_REPO_ROOT       = Path(__file__).resolve().parents[2]          # IncidentIQ/
KNOWLEDGE_BASE   = _REPO_ROOT / "knowledge_base"                # IncidentIQ/knowledge_base/
FAISS_INDEX_PATH = _REPO_ROOT / "src" / "rag" / "faiss_index"  # IncidentIQ/src/rag/faiss_index/

CHUNK_SIZE      = 800
CHUNK_OVERLAP   = 100
TOP_K           = 5
SCORE_THRESHOLD = 0.4   # below this → "low" confidence

# ── Model init (lazy — only if OPENROUTER_API_KEY is set) ─────────────────────
def _get_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="openai/gpt-4o-mini",
        openai_api_key=os.environ["OPENROUTER_API_KEY"],
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0,
    )

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a DevOps incident analysis assistant.
Using ONLY the context below (past incident reports, SOPs, runbooks),
answer the question concisely and precisely.
If the context does not contain enough information, say so clearly.

Context:
{context}

Question:
{question}

Answer (include root cause, resolution steps, and relevant SOP references):""",
)

# ─────────────────────────────────────────────────────────────────────────────
# Ingestion  (run once to build the FAISS index from knowledge_base/)
# ─────────────────────────────────────────────────────────────────────────────
def ingest(knowledge_base_dir: Optional[Path] = None, index_path: Optional[Path] = None) -> None:
    """
    Load all .txt and .pdf files from knowledge_base/, embed them, and
    save a FAISS index to src/rag/faiss_index/.

    Call this once before running the notebook pipeline, or whenever you add
    new documents to knowledge_base/.

    Usage (from repo root):
        python -c "from src.rag.rag_retriever import ingest; ingest()"
    """
    kb_dir  = knowledge_base_dir or KNOWLEDGE_BASE
    idx_dir = index_path or FAISS_INDEX_PATH

    import glob
    all_docs = []
    pattern  = str(kb_dir / "**" / "*.*")
    files    = glob.glob(pattern, recursive=True)

    if not files:
        raise FileNotFoundError(
            f"No files found under '{kb_dir}'. "
            "Add .txt or .pdf documents to the knowledge_base/ folder."
        )

    for fp in files:
        if not Path(fp).is_file():
            continue
        ext = Path(fp).suffix.lower()
        try:
            if ext == ".txt":
                loader = TextLoader(fp, encoding="utf-8")
            elif ext == ".pdf":
                loader = PyPDFLoader(fp)
            else:
                print(f"  [SKIP] {fp}")
                continue
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = fp
            all_docs.extend(docs)
            print(f"  [LOAD] {fp}  ({len(docs)} doc(s))")
        except Exception as e:
            print(f"  [ERROR] {fp}: {e}")

    print(f"\n✅  Loaded {len(all_docs)} document(s)")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(all_docs)
    print(f"✅  Split into {len(chunks)} chunk(s)")

    print("⏳  Embedding and building FAISS index …")
    embeddings  = _get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    idx_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(idx_dir))
    print(f"✅  FAISS index saved to '{idx_dir}'")


def _load_vectorstore() -> FAISS:
    if not FAISS_INDEX_PATH.exists():
        raise FileNotFoundError(
            f"FAISS index not found at '{FAISS_INDEX_PATH}'. "
            "Run ingest() first:  python -c \"from src.rag.rag_retriever import ingest; ingest()\""
        )
    return FAISS.load_local(
        str(FAISS_INDEX_PATH),
        _get_embeddings(),
        allow_dangerous_deserialization=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Query builder  — converts an EvidenceCluster dict into a rich search query
# ─────────────────────────────────────────────────────────────────────────────
def _build_query(cluster: Dict[str, Any]) -> str:
    """
    The notebook's Classifier Agent already structured the cluster for us.
    We extract the most signal-rich fields to form a natural-language query.
    """
    category  = cluster.get("candidate_category", "unknown")
    services  = ", ".join(cluster.get("affected_services", [])) or "unknown service"
    severity  = cluster.get("severity_hint", "unknown")
    signature = cluster.get("signature", "")
    # Pull top evidence messages for richer semantic search
    evidence_text = " | ".join(
        e.get("message", "")
        for e in cluster.get("evidence", [])[:5]
        if e.get("message")
    )
    return (
        f"Incident type: {category}\n"
        f"Affected services: {services}\n"
        f"Severity: {severity}\n"
        f"Signal signature: {signature}\n"
        f"Evidence: {evidence_text}"
    )

# ─────────────────────────────────────────────────────────────────────────────
# Per-cluster retrieval  — returns chunks in the format the notebook expects
# ─────────────────────────────────────────────────────────────────────────────
def _retrieve_for_cluster(
    cluster: Dict[str, Any],
    vectorstore: FAISS,
    top_k: int = TOP_K,
) -> List[Dict[str, Any]]:
    """
    Retrieve the top-K most relevant runbook/SOP chunks for one cluster.

    Returns a list of dicts that mirror the embedded RUNBOOKS format so the
    fallback_remediation_agent() in the notebook can consume them unchanged:
        [{"title", "source", "score", "diagnostics", "remediation",
          "validation", "safety_notes", "rag_answer"}, ...]
    """
    query   = _build_query(cluster)
    results = vectorstore.similarity_search_with_relevance_scores(query, k=top_k)

    chunks = []
    top_score = 0.0
    for doc, score in results:
        top_score = max(top_score, score)
        chunks.append({
            "title":       Path(doc.metadata.get("source", "unknown")).name,
            "source":      doc.metadata.get("source", "unknown"),
            "score":       round(score, 4),
            "content":     doc.page_content,
            # These keys are read by fallback_remediation_agent() — populate
            # with empty lists; the LLM synthesised answer goes in rag_answer.
            "diagnostics":   [],
            "remediation":   [],
            "validation":    [],
            "safety_notes":  [],
            "incident_type": cluster.get("candidate_category", ""),
            "symptoms":      [],
        })

    # Sort best first
    chunks.sort(key=lambda x: x["score"], reverse=True)

    # filter out chunks if they score less than SCORE_THRESHOLD
    chunks = [c for c in chunks if c["score"] >= SCORE_THRESHOLD] or chunks[:1]

    # LLM-synthesised answer over all retrieved chunks (optional, needs API key)
    if os.getenv("OPENROUTER_API_KEY") and chunks:
        try:
            retriever  = vectorstore.as_retriever(search_kwargs={"k": top_k})
            qa_chain   = RetrievalQA.from_chain_type(
                llm=_get_llm(),
                chain_type="stuff",
                retriever=retriever,
                chain_type_kwargs={"prompt": RAG_PROMPT},
            )
            rag_answer = qa_chain.invoke({"query": query})["result"]
            # Inject the synthesised answer into the top chunk so the
            # Remediation Agent has a ready-made summary to use.
            if chunks:
                chunks[0]["rag_answer"] = rag_answer
        except Exception as e:
            print(f"  [RAG LLM warning] {e}")

    return chunks

# ─────────────────────────────────────────────────────────────────────────────
# Public interface  — called by retrieve_runbook_context in the notebook
# ─────────────────────────────────────────────────────────────────────────────
def retrieve_rag_context(analysis_context: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Main entry point.  Matches the signature the notebook expects:

    Input:
        {"run_id": str, "clusters": [EvidenceCluster as dict, ...]}

    Output:
        {cluster_id: [runbook_chunk_dict, ...], ...}

    Falls back gracefully to an empty dict if the FAISS index is not ready,
    so the notebook's embedded RUNBOOKS fallback still kicks in.
    """
    if not os.getenv("OPENROUTER_API_KEY"):
        print("  [RAG] No OPENROUTER_API_KEY found — skipping FAISS retrieval, notebook fallback will run.")
        return {}

    try:
        vectorstore = _load_vectorstore()
    except FileNotFoundError as e:
        print(f"  [RAG] {e}")
        print("  [RAG] Falling back to notebook embedded runbooks.")
        return {}

    rag_context: Dict[str, List[Dict[str, Any]]] = {}
    for cluster in analysis_context.get("clusters", []):
        cluster_id = cluster.get("cluster_id", "unknown")
        try:
            rag_context[cluster_id] = _retrieve_for_cluster(cluster, vectorstore)
            print(f"  [RAG] {cluster_id} → {len(rag_context[cluster_id])} chunk(s) retrieved")
        except Exception as e:
            print(f"  [RAG] {cluster_id} retrieval error: {e}")
            rag_context[cluster_id] = []

    return rag_context