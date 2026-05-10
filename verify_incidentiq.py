import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load env vars
load_dotenv()

def verify_setup():
    print("🚀 IncidentIQ: Starting Full Pipeline Verification...\n")
    
    # 1. Check RAG Retrieval
    print("📂 [1/3] Testing RAG (FAISS) Retrieval...")
    try:
        from src.rag.retriever import retrieve_rag_context
        chunks = retrieve_rag_context("Database", "hikari_timeout")
        if chunks and "SOP" in chunks[0]["title"]:
            print("✅ RAG: Successfully retrieved runbook context from FAISS.\n")
        else:
            print("⚠️ RAG: Retrieval worked but returned default/empty data.\n")
    except Exception as e:
        print(f"❌ RAG Error: {e}\n")

    # 2. Check n8n Integration
    print("🔗 [2/3] Testing n8n Webhooks...")
    from src.integrations.n8n import send_incident_to_n8n
    mock_incident = {
        "incident_id": "TEST-001",
        "severity": "P1",
        "category": "Database",
        "title": "Smoke Test: Verification in progress",
        "affected_services": ["test-service"],
        "remediation": {"immediate_actions": ["Verify n8n connection"]}
    }
    # Note: This will actually send a test message if URLs are in .env
    results = send_incident_to_n8n(mock_incident)
    print(f"✅ n8n Results: Slack: {results.get('slack')}, JIRA: {results.get('jira')}\n")

    # 3. Check Full Graph Pipeline
    print("🧠 [3/3] Testing Full Graph Pipeline (13-Node Flow)...")
    try:
        from src.graph.builder import analyze_uploaded_logs
        # Create a tiny mock log file
        mock_log = "2026-05-10T12:00:00Z ERROR payment-api hikaripool connection timeout"
        mock_path = "smoke_test.log"
        with open(mock_path, "w") as f: f.write(mock_log)
        
        # Run analysis
        response = analyze_uploaded_logs([mock_path])
        
        if response.get("status") == "completed" and response.get("incidents"):
            print(f"✅ Pipeline: Successfully processed logs.")
            print(f"   Found {len(response['incidents'])} incident(s).")
            print(f"   Highest Severity: {response['summary']['highest_severity']}")
            print(f"   Steps Completed: {response['summary']['steps_completed']}")
        else:
            print("❌ Pipeline: Analysis failed or returned no incidents.")
            
        if os.path.exists(mock_path): os.remove(mock_path)
    except Exception as e:
        print(f"❌ Pipeline Error: {e}")

    print("\n✨ Verification Complete! Check your Slack/JIRA for the 'Smoke Test' message.")

if __name__ == "__main__":
    verify_setup()
