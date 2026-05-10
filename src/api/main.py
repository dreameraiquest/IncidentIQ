import sys
import os
from pathlib import Path

# Add the project root to sys.path so we can import from src
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import List, Optional
import shutil
from dotenv import load_dotenv
from src import analyze_uploaded_logs, AnalysisResponse

# Load environment variables
load_dotenv()

app = FastAPI(
    title="IncidentIQ API",
    description="FastAPI backend for IncidentIQ log analysis platform",
    version="1.0.0"
)

# Ensure a temporary directory for initial uploads exists
TEMP_DIR = Path("temp_uploads")
TEMP_DIR.mkdir(exist_ok=True)

# RAG Environment Check
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("[RAG] No OPENROUTER_API_KEY found — skipping FAISS retrieval, notebook fallback will run.")

@app.get("/health")
async def health():
    """Health check endpoint."""
    health_status = {"status": "healthy", "service": "IncidentIQ"}
    if not os.getenv("OPENROUTER_API_KEY"):
        health_status["warnings"] = ["[RAG] No OPENROUTER_API_KEY found — skipping FAISS retrieval, notebook fallback will run."]
    return health_status

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    files: List[UploadFile] = File(...),
    enable_rag: bool = Form(True),
    run_evals: bool = Form(True),
    max_clusters: int = Form(25),
    max_evidence_per_cluster: int = Form(25)
):
    """
    Upload logs and analyze them for incidents.
    """
    saved_paths = []
    try:
        # Save uploaded files to a temporary directory
        for upload_file in files:
            temp_path = TEMP_DIR / upload_file.filename
            with temp_path.open("wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
            saved_paths.append(str(temp_path))
        
        # Call the analysis pipeline
        response = analyze_uploaded_logs(
            saved_paths,
            options={
                "enable_rag": enable_rag,
                "run_evals": run_evals,
                "max_clusters": max_clusters,
                "max_evidence_per_cluster": max_evidence_per_cluster,
                "preview_only": True,
                "enable_real_integrations": False,
            }
        )
        
        return response

    except Exception as e:
        # In a real app, we'd log the error here
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary files
        for path in saved_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
