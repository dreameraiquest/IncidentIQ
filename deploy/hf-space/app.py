import os
from typing import Any, Iterable, Optional

import gradio as gr
from dotenv import load_dotenv

load_dotenv()

from src import analyze_uploaded_logs, response_to_markdown


APP_TITLE = os.getenv("APP_TITLE", "IncidentIQ")
APP_DESCRIPTION = os.getenv(
    "APP_DESCRIPTION",
    "Upload raw DevOps logs or a ZIP. IncidentIQ parses the evidence, detects "
    "incident candidates, retrieves local runbooks, and generates preview-only "
    "tickets, notifications, cookbooks, and reports.",
)
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://jira.example.com")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "OPS")
GRADIO_ANALYTICS_ENABLED = os.getenv("GRADIO_ANALYTICS_ENABLED", "false").lower() == "true"


def _progress_markdown(active_step: int, extra: str = "") -> str:
    steps = [
        "Receive uploaded report/log file",
        "Copy upload into an isolated run folder",
        "Extract ZIP safely and discover runtime log files",
        "Parse and normalize log lines",
        "Extract incident signals",
        "Cluster related evidence",
        "Retrieve local RAG runbooks",
        "Run classifier, timeline, RCA, remediation, and critic agents",
        "Build preview Jira tickets, Slack updates, cookbooks, and reports",
        "Render final result",
    ]
    lines = ["## Backend Progress", ""]
    for idx, label in enumerate(steps, start=1):
        if idx < active_step:
            marker = "[done]"
        elif idx == active_step:
            marker = "[running]"
        else:
            marker = "[waiting]"
        lines.append(f"- `{marker}` {label}")
    if extra:
        lines.extend(["", extra])
    return "\n".join(lines)


def _file_paths(files: Any) -> list[str]:
    if not files:
        return []
    file_list = files if isinstance(files, list) else [files]
    paths = []
    for item in file_list:
        if isinstance(item, str):
            paths.append(item)
        elif hasattr(item, "name"):
            paths.append(str(item.name))
        elif isinstance(item, dict) and item.get("name"):
            paths.append(str(item["name"]))
    return paths


def _jira_links_markdown(response) -> str:
    if not response.incidents:
        return "## Jira Links\nNo incident candidates were found, so no Jira previews were generated."
    lines = ["## Jira Links", ""]
    for idx, incident in enumerate(response.incidents, start=1):
        issue_key = f"{JIRA_PROJECT_KEY}-{1000 + idx}"
        url = f"{JIRA_BASE_URL.rstrip('/')}/browse/{issue_key}?incident_id={incident.incident_id}"
        lines.append(f"- [{issue_key}: {incident.severity} {incident.category}]({url}) - dummy preview link")
    return "\n".join(lines)


def analyze_with_progress(
    files: Any,
    enable_rag: bool,
    run_evals: bool,
    max_clusters: int,
) -> Iterable[tuple[str, str, str, Optional[str], Optional[str], Optional[str], Optional[str]]]:
    paths = _file_paths(files)
    empty_files = (None, None, None, None)
    if not paths:
        yield (
            _progress_markdown(1, "Upload at least one `.zip`, `.jsonl`, `.log`, `.txt`, or `.json` file."),
            "",
            "",
            *empty_files,
        )
        return

    yield (_progress_markdown(1, f"Received `{len(paths)}` file(s)."), "", "", *empty_files)
    yield (_progress_markdown(2), "", "", *empty_files)
    yield (_progress_markdown(3), "", "", *empty_files)
    yield (_progress_markdown(4), "", "", *empty_files)
    yield (_progress_markdown(5), "", "", *empty_files)
    yield (_progress_markdown(6), "", "", *empty_files)
    yield (_progress_markdown(7), "", "", *empty_files)
    yield (_progress_markdown(8), "", "", *empty_files)

    try:
        response = analyze_uploaded_logs(
            paths,
            options={
                "enable_rag": bool(enable_rag),
                "run_evals": bool(run_evals),
                "max_clusters": int(max_clusters),
                "max_evidence_per_cluster": 25,
                "preview_only": True,
                "enable_real_integrations": False,
            },
        )
    except Exception as exc:
        yield (_progress_markdown(8, f"Analysis failed: `{exc}`"), "", "", *empty_files)
        return

    yield (
        _progress_markdown(9),
        response_to_markdown(response),
        _jira_links_markdown(response),
        response.reports.get("output_zip"),
        response.reports.get("json"),
        response.reports.get("markdown"),
        response.reports.get("csv"),
    )
    yield (
        _progress_markdown(10, f"Completed run `{response.run_id}`."),
        response_to_markdown(response),
        _jira_links_markdown(response),
        response.reports.get("output_zip"),
        response.reports.get("json"),
        response.reports.get("markdown"),
        response.reports.get("csv"),
    )


def build_demo() -> gr.Blocks:
    theme = gr.themes.Soft(primary_hue="blue", neutral_hue="slate")
    with gr.Blocks(title=APP_TITLE, theme=theme, analytics_enabled=GRADIO_ANALYTICS_ENABLED) as demo:
        gr.Markdown(f"# {APP_TITLE}\n{APP_DESCRIPTION}")
        files = gr.File(
            label="Upload report/log file",
            file_count="multiple",
            file_types=[".zip", ".jsonl", ".log", ".txt", ".json"],
        )
        enable_rag = gr.Checkbox(value=True, label="Use local RAG runbooks")
        run_evals = gr.Checkbox(value=True, label="Run eval if ground truth is included")
        max_clusters = gr.Slider(1, 100, value=25, step=1, label="Max clusters")
        analyze_btn = gr.Button("Analyze", variant="primary")
        progress = gr.Markdown(value=_progress_markdown(0), label="Backend Progress")
        result = gr.Markdown(label="Final Result")
        jira_links = gr.Markdown(label="Jira Links")
        output_zip = gr.File(label="Output ZIP")
        output_json = gr.File(label="JSON")
        output_md = gr.File(label="Markdown")
        output_csv = gr.File(label="CSV")

        analyze_btn.click(
            analyze_with_progress,
            inputs=[files, enable_rag, run_evals, max_clusters],
            outputs=[progress, result, jira_links, output_zip, output_json, output_md, output_csv],
            api_name="analyze",
        )
    return demo


demo = build_demo()


if __name__ == "__main__":
    server_name = os.getenv("GRADIO_SERVER_NAME")
    raw_port = os.getenv("PORT") or os.getenv("GRADIO_SERVER_PORT")
    launch_kwargs = {"server_name": server_name}
    if raw_port:
        launch_kwargs["server_port"] = int(raw_port)
    demo.launch(**launch_kwargs)
