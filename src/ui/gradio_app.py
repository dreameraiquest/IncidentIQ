import gradio as gr
import json
import os
import sys
from pathlib import Path
from typing import Iterable, Optional, Any, List

# Add the project root to sys.path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.graph.builder import analyze_uploaded_logs
from src.reporting.markdown_report import response_to_markdown
from src.models.incident import IncidentResult

APP_TITLE = "IncidentIQ Dashboard"
APP_DESCRIPTION = "Multi-Agent AI Platform for DevOps Incident Analysis, RCA & Automated Response"

def _progress_markdown(active_step: int, extra: str = "") -> str:
    steps = [
        "Receive uploaded log files",
        "Normalize and parse log events",
        "Extract operational signals",
        "Cluster related evidence",
        "Retrieve RAG context (FAISS)",
        "Run Multi-Agent reasoning (Classifier, RCA, Timeline)",
        "Perform Critic review & Validation",
        "Trigger n8n integrations (Optional)",
        "Generate final reports and exports",
    ]
    lines = ["### 🔄 Backend Progress", ""]
    for idx, label in enumerate(steps, start=1):
        if idx < active_step: marker = "✅"
        elif idx == active_step: marker = "⏳"
        else: marker = "⚪️"
        lines.append(f"- {marker} {label}")
    if extra: lines.append(f"\n> {extra}")
    return "\n".join(lines)

def process_logs_with_progress(files, demo_mode):
    if not files and not demo_mode:
        yield _progress_markdown(1, "❌ Please upload files."), "", "", None, None
        return

    # Step 1: Start
    yield _progress_markdown(1, "Starting analysis..."), "{}", "", None, None
    
    # Simulate progress for smooth UI (Steps 2-7)
    for i in range(2, 8):
        yield _progress_markdown(i), "{}", "", None, None

    # Step 8: Real Analysis
    try:
        file_paths = [f.name for f in files] if files else []
        # For demo mode, we'd normally point to a specific file
        response = analyze_uploaded_logs(file_paths)
        
        # Convert dicts back to Pydantic models for the report builder
        incidents = [IncidentResult(**i) for i in response.get("incidents", [])]
        
        md_report = response_to_markdown(incidents, response["summary"])
        
        # Files for download
        json_path = os.path.join(response["run_id"], "analysis_response.json") # This is a placeholder
        
        yield (
            _progress_markdown(9, "Analysis Complete!"),
            json.dumps(response, indent=2),
            md_report,
            None, # JSON file placeholder
            None  # Report file placeholder
        )
    except Exception as e:
        yield _progress_markdown(8, f"❌ Error: {str(e)}"), "{}", f"Error: {e}", None, None

def trigger_n8n_ui(results_json):
    if not results_json or results_json == "{}":
        return "### ❌ No results to send. Run analysis first."
    try:
        data = json.loads(results_json)
        incidents = data.get("incidents", [])
        if not incidents: return "### ⚠️ No incidents found to notify."
        
        from src.integrations.n8n import notify_all_incidents
        results = notify_all_incidents(incidents)
        
        output = "### 🚀 n8n Integration Status\n"
        for res in results:
            s = res['status']
            output += f"- **{res['incident_id']}**: Slack: `{s['slack']}`, JIRA: `{s['jira']}`\n"
        return output
    except Exception as e:
        return f"### ❌ Error: {str(e)}"

def build_app():
    theme = gr.themes.Soft(primary_hue="blue", neutral_hue="slate")
    
    with gr.Blocks(title=APP_TITLE) as demo:
        gr.Markdown(f"# 🚨 {APP_TITLE}")
        gr.Markdown(APP_DESCRIPTION)
        
        with gr.Row():
            with gr.Column(scale=1):
                log_files = gr.File(file_count="multiple", label="Upload Logs (.log, .txt, .zip)")
                demo_checkbox = gr.Checkbox(label="Demo Mode", value=False)
                analyze_btn = gr.Button("🔍 Run Analysis", variant="primary")
                n8n_btn = gr.Button("🚀 Trigger n8n Dispatch", variant="secondary")
                
                progress_area = gr.Markdown(_progress_markdown(0))

            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.TabItem("📊 Analysis Report"):
                        report_output = gr.Markdown("Analysis report will appear here...")
                    with gr.TabItem("📄 Raw JSON"):
                        json_output = gr.Code(language="json")
                    with gr.TabItem("🔗 Integrations"):
                        n8n_status = gr.Markdown("Trigger n8n to see status...")
                
                with gr.Row():
                    download_json = gr.File(label="Download JSON")
                    download_md = gr.File(label="Download Report")

        analyze_btn.click(
            fn=process_logs_with_progress,
            inputs=[log_files, demo_checkbox],
            outputs=[progress_area, json_output, report_output, download_json, download_md]
        )
        
        n8n_btn.click(
            fn=trigger_n8n_ui,
            inputs=[json_output],
            outputs=n8n_status
        )

    return demo

if __name__ == "__main__":
    app = build_app()
    theme = gr.themes.Soft(primary_hue="blue", neutral_hue="slate")
    app.launch(server_name="0.0.0.0", server_port=7860, theme=theme)
