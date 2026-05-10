"""
gradio_app.py — IncidentIQ Dashboard v3.1
• Auto n8n dispatch (no checkbox)
• LLM-as-Judge Evals tab with smart GT matching
• Shows exact vs inexact GT match badges per incident
• OpenRouter judge
"""

import gradio as gr
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.graph.builder import analyze_uploaded_logs
from src.reporting.markdown_report import response_to_markdown
from src.models.incident import IncidentResult
from src.integrations.n8n import notify_all_incidents
from src.evals.evaluator import evaluate_all, WEIGHTS, AXIS_LABELS, DEFAULT_GROUND_TRUTH

APP_TITLE   = "IncidentIQ"
APP_SUBTITLE = "Multi-Agent AI Platform · DevOps Incident Analysis · LLM-as-Judge Evals"

# ─────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;700;800&display=swap');

:root {
    --bg-base:   #0a0c10;
    --bg-card:   #111318;
    --bg-raised: #181b22;
    --border:    #252830;
    --accent:    #3b82f6;
    --accent-g:  #3b82f640;
    --green:     #22c55e;
    --amber:     #f59e0b;
    --red:       #ef4444;
    --purple:    #a78bfa;
    --text-1:    #f1f5f9;
    --text-2:    #94a3b8;
    --text-3:    #475569;
    --mono:      'JetBrains Mono', monospace;
    --display:   'Syne', sans-serif;
}

body, .gradio-container {
    background: var(--bg-base) !important;
    font-family: var(--mono) !important;
}
.gradio-container {
    max-width: 1440px !important;
    margin: 0 auto !important;
    padding: 24px !important;
}
.iq-header {
    padding: 28px 32px;
    background: linear-gradient(135deg, #111318, #0f1318);
    border: 1px solid var(--border);
    border-radius: 12px; margin-bottom: 20px;
    position: relative; overflow: hidden;
}
.iq-header::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
}
.iq-title {
    font-family: var(--display); font-size: 26px;
    font-weight: 800; color: var(--text-1); margin: 0;
}
.iq-sub   { font-size: 12px; color: var(--text-2); margin: 4px 0 0 0; }
.iq-badge {
    background: var(--accent); color: #fff;
    font-size: 11px; font-weight: 700; letter-spacing: 2px;
    padding: 3px 10px; border-radius: 4px; text-transform: uppercase;
}
.run-btn {
    background: var(--accent) !important; border: none !important;
    border-radius: 8px !important; font-family: var(--mono) !important;
    font-size: 13px !important; font-weight: 700 !important;
    letter-spacing: 1px !important; color: #fff !important;
    height: 52px !important; box-shadow: 0 0 24px var(--accent-g) !important;
    transition: all .2s !important;
}
.run-btn:hover { transform: translateY(-1px) !important; box-shadow: 0 0 40px var(--accent-g) !important; }
.tabs button { font-family: var(--mono) !important; font-size: 12px !important; }
button.selected { border-bottom: 2px solid var(--accent) !important; color: var(--accent) !important; }
.prose-report { font-family: var(--mono); font-size: 13px; color: var(--text-1); line-height: 1.7; }
"""

# ─────────────────────────────────────────────────────────────
# Static HTML
# ─────────────────────────────────────────────────────────────
def _pill(icon, label, sub, border="#252830", text_color="#f1f5f9"):
    return (
        f'<div style="background:#181b22;border:1px solid {border};border-radius:6px;padding:10px 12px;">'
        f'<div style="font-size:16px;margin-bottom:4px;">{icon}</div>'
        f'<div style="font-size:10px;font-weight:700;color:{text_color};letter-spacing:1px;text-transform:uppercase;">{label}</div>'
        f'<div style="font-size:11px;color:#64748b;margin-top:2px;">{sub}</div>'
        f'</div>'
    )

STRATEGY_HTML = (
    '<div style="background:#111318;border:1px solid #252830;border-radius:10px;padding:20px;margin-bottom:16px;">'
    '<div style="font-family:\'Syne\',sans-serif;font-size:12px;font-weight:700;color:#64748b;'
    'letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;">🧠 Analysis Strategy</div>'
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">'
    + _pill("📥", "Ingest", ".log .txt .zip .jsonl")
    + _pill("🔍", "Signals", "Regex + Pydantic")
    + _pill("📚", "RAG (FAISS)", "Runbook retrieval")
    + _pill("🤖", "Multi-Agent", "RCA · Timeline · Critic")
    + _pill("🚀", "Auto n8n", "Slack · JIRA", border="#1d4ed855", text_color="#60a5fa")
    + _pill("🧪", "LLM Judge", "5-axis · OpenRouter", border="#7c3aed55", text_color="#a78bfa")
    + '</div>'
    '<div style="margin-top:12px;background:linear-gradient(90deg,#1e3a5f,#1a2f4a);'
    'border:1px solid #2563eb55;border-radius:8px;padding:10px 16px;font-size:12px;color:#93c5fd;'
    'display:flex;align-items:center;gap:10px;">'
    '<span style="width:8px;height:8px;background:#3b82f6;border-radius:50%;box-shadow:0 0 8px #3b82f6;'
    'display:inline-block;flex-shrink:0;"></span>'
    'n8n dispatch and LLM-as-Judge evaluation run <strong style="color:#fff;">automatically</strong> after every analysis.'
    '</div></div>'
)

PIPELINE_HTML = (
    '<div style="font-family:\'JetBrains Mono\',monospace;font-size:11px;color:#475569;line-height:2.1;'
    'padding:12px 16px;background:#0d1117;border:1px solid #1e2533;border-radius:8px;margin-top:8px;">'
    '<span style="color:#3b82f6;">run_analysis</span><br/>'
    '&nbsp;&nbsp;→ <span style="color:#94a3b8;">parse_raw_files</span><br/>'
    '&nbsp;&nbsp;→ <span style="color:#94a3b8;">extract_signals</span><br/>'
    '&nbsp;&nbsp;→ <span style="color:#94a3b8;">build_evidence_clusters</span><br/>'
    '&nbsp;&nbsp;→ <span style="color:#60a5fa;">retrieve_runbook_context <span style="color:#22c55e;">[FAISS]</span></span><br/>'
    '&nbsp;&nbsp;→ <span style="color:#94a3b8;">run_incident_agents</span><br/>'
    '&nbsp;&nbsp;→ <span style="color:#94a3b8;">critic_review</span><br/>'
    '&nbsp;&nbsp;→ <span style="color:#f59e0b;">notify_all_incidents <span style="color:#60a5fa;">[n8n auto]</span></span><br/>'
    '&nbsp;&nbsp;→ <span style="color:#a78bfa;">evaluate_all <span style="color:#7c3aed;">[LLM judge · OpenRouter]</span></span><br/>'
    '&nbsp;&nbsp;→ <span style="color:#94a3b8;">export_results</span>'
    '</div>'
)

# ─────────────────────────────────────────────────────────────
# Progress
# ─────────────────────────────────────────────────────────────
STEPS = [
    ("📥", "Receive uploaded log files"),
    ("🔄", "Normalize and parse log events"),
    ("🔍", "Extract operational signals"),
    ("🗂️",  "Cluster related evidence"),
    ("📚", "Retrieve RAG context (FAISS)"),
    ("🤖", "Run Multi-Agent reasoning"),
    ("🧐", "Critic review & Validation"),
    ("🚀", "n8n dispatch — Slack + JIRA"),
    ("🧪", "LLM-as-Judge evaluation"),
    ("📊", "Export reports & results"),
]

def _progress_html(active: int, note: str = "") -> str:
    rows = [
        '<div style="font-family:\'JetBrains Mono\',monospace;">',
        '<div style="font-size:11px;font-weight:700;color:#475569;letter-spacing:2px;'
        'text-transform:uppercase;margin-bottom:12px;">Pipeline Progress</div>',
    ]
    for idx, (icon, label) in enumerate(STEPS, 1):
        if idx < active:    c, t = "#22c55e", "✓"
        elif idx == active: c, t = "#f59e0b", "▶"
        else:               c, t = "#334155", "○"
        rows.append(
            f'<div style="display:flex;align-items:center;gap:10px;padding:5px 0;font-size:12px;color:{c};">'
            f'<span style="width:14px;text-align:center;font-weight:700;">{t}</span>'
            f'<span>{icon} {label}</span></div>'
        )
    if note:
        rows.append(
            f'<div style="margin-top:10px;padding:8px 12px;background:#0f172a;'
            f'border-left:3px solid #3b82f6;border-radius:0 6px 6px 0;'
            f'font-size:12px;color:#94a3b8;">{note}</div>'
        )
    rows.append("</div>")
    return "\n".join(rows)

# ─────────────────────────────────────────────────────────────
# n8n renderers
# ─────────────────────────────────────────────────────────────
def _n8n_empty():
    return ('<div style="font-family:\'JetBrains Mono\',monospace;color:#334155;'
            'font-size:13px;padding:32px;text-align:center;">'
            '🚀 n8n dispatch runs automatically after analysis.</div>')

def _badge(val: str) -> str:
    v = val.lower()
    if "success" in v:
        return (f'<span style="background:#16a34a22;color:#22c55e;border:1px solid #16a34a44;'
                f'border-radius:4px;padding:2px 8px;font-size:11px;font-weight:700;">✓ {val}</span>')
    if "skip" in v:
        return (f'<span style="background:#92400e22;color:#f59e0b;border:1px solid #92400e44;'
                f'border-radius:4px;padding:2px 8px;font-size:11px;">⊘ {val}</span>')
    return (f'<span style="background:#7f1d1d22;color:#ef4444;border:1px solid #7f1d1d44;'
            f'border-radius:4px;padding:2px 8px;font-size:11px;">✗ {val}</span>')

def _n8n_html(results: list) -> str:
    rows = [
        '<div style="font-family:\'JetBrains Mono\',monospace;">',
        '<div style="font-size:11px;font-weight:700;color:#475569;letter-spacing:2px;'
        'text-transform:uppercase;margin-bottom:12px;">🚀 Automated n8n Dispatch</div>',
    ]
    for r in results:
        rows.append(
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:8px 12px;background:#181b22;border:1px solid #252830;'
            f'border-radius:6px;margin-bottom:6px;">'
            f'<span style="color:#94a3b8;font-size:12px;">{r["incident_id"]}</span>'
            f'<span style="display:flex;gap:8px;align-items:center;">'
            f'<span style="color:#475569;font-size:11px;">Slack</span>{_badge(r["status"]["slack"])}'
            f'<span style="color:#475569;font-size:11px;margin-left:8px;">JIRA</span>{_badge(r["status"]["jira"])}'
            f'</span></div>'
        )
    rows.append("</div>")
    return "\n".join(rows)

# ─────────────────────────────────────────────────────────────
# Eval renderers
# ─────────────────────────────────────────────────────────────
def _score_color(score_0_100: float) -> str:
    if score_0_100 >= 70: return "#22c55e"
    if score_0_100 >= 40: return "#f59e0b"
    return "#ef4444"

def _axis_bar(score_0_10: float) -> str:
    pct   = score_0_10 * 10
    color = _score_color(pct)
    return (
        f'<div style="flex:1;height:5px;background:#1e293b;border-radius:3px;overflow:hidden;">'
        f'<div style="width:{pct}%;height:100%;background:{color};border-radius:3px;"></div>'
        f'</div>'
    )

def _match_badge(exact: bool, gt_id: str) -> str:
    if exact:
        return (
            f'<span style="background:#16a34a22;color:#22c55e;border:1px solid #16a34a44;'
            f'border-radius:4px;padding:2px 8px;font-size:10px;font-weight:700;">✓ exact match · {gt_id}</span>'
        )
    return (
        f'<span style="background:#92400e22;color:#f59e0b;border:1px solid #92400e44;'
        f'border-radius:4px;padding:2px 8px;font-size:10px;">⚠ closest GT · {gt_id}</span>'
    )

def _eval_empty():
    return ('<div style="font-family:\'JetBrains Mono\',monospace;color:#334155;'
            'font-size:13px;padding:32px;text-align:center;">'
            '🧪 LLM-as-Judge evaluation runs automatically after analysis.</div>')

def _eval_html(ev_result: dict) -> str:
    if not ev_result:
        return _eval_empty()

    mean    = ev_result.get("mean_score", 0)
    total   = ev_result.get("total_evaluated", 0)
    exact   = ev_result.get("exact_gt_matches", 0)
    inexact = ev_result.get("inexact_gt_matches", 0)
    evals   = ev_result.get("incident_evals", [])
    mc      = _score_color(mean)

    html = ['<div style="font-family:\'JetBrains Mono\',monospace;">']

    # ── Summary bar ───────────────────────────────────────────────────────
    html.append(
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:16px;">'

        # Mean score
        f'<div style="padding:16px 20px;background:#111318;border:1px solid #252830;border-radius:10px;">'
        f'<div style="font-size:11px;color:#64748b;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;">Mean Score</div>'
        f'<div style="font-size:38px;font-weight:700;color:{mc};font-family:\'Syne\',sans-serif;line-height:1;">'
        f'{mean}<span style="font-size:16px;color:#475569;">/100</span></div>'
        f'</div>'

        # Incidents evaluated
        f'<div style="padding:16px 20px;background:#111318;border:1px solid #252830;border-radius:10px;">'
        f'<div style="font-size:11px;color:#64748b;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;">Evaluated</div>'
        f'<div style="font-size:38px;font-weight:700;color:#94a3b8;font-family:\'Syne\',sans-serif;line-height:1;">{total}</div>'
        f'</div>'

        # GT match quality
        f'<div style="padding:16px 20px;background:#111318;border:1px solid #252830;border-radius:10px;">'
        f'<div style="font-size:11px;color:#64748b;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">GT Match Quality</div>'
        f'<div style="display:flex;gap:8px;align-items:center;">'
        f'<span style="background:#16a34a22;color:#22c55e;border:1px solid #16a34a44;border-radius:4px;padding:3px 8px;font-size:12px;font-weight:700;">✓ {exact} exact</span>'
        f'<span style="background:#92400e22;color:#f59e0b;border:1px solid #92400e44;border-radius:4px;padding:3px 8px;font-size:12px;">⚠ {inexact} closest</span>'
        f'</div>'
        f'<div style="font-size:10px;color:#475569;margin-top:6px;">Closest = no exact GT category found</div>'
        f'</div>'

        f'</div>'
    )

    # ── Weight legend ─────────────────────────────────────────────────────
    html.append('<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-bottom:16px;">')
    for ax, (icon, label) in AXIS_LABELS.items():
        w_pct = int(WEIGHTS[ax] * 100)
        html.append(
            f'<div style="background:#181b22;border:1px solid #252830;border-radius:6px;'
            f'padding:8px 10px;text-align:center;">'
            f'<div style="font-size:14px;">{icon}</div>'
            f'<div style="font-size:10px;color:#f1f5f9;font-weight:700;margin:2px 0;">{label}</div>'
            f'<div style="font-size:10px;color:#475569;">weight {w_pct}%</div>'
            f'</div>'
        )
    html.append('</div>')

    # ── Per-incident cards ────────────────────────────────────────────────
    for ev in evals:
        inc_id  = ev.get("incident_id", "?")
        cat     = ev.get("category", "?")
        sev     = ev.get("severity", "?")
        gt_id   = ev.get("matched_gt_id", "?")
        exact_m = ev.get("exact_match", False)
        overall = ev.get("overall_score", 0)
        verdict = ev.get("verdict", "")
        axes    = ev.get("axes", {})
        oc      = _score_color(overall)

        # Severity badge colour
        sev_colors = {"P1": "#ef4444", "P2": "#f59e0b", "P3": "#22c55e"}
        sev_c = sev_colors.get(sev.upper(), "#94a3b8")

        html.append(
            # card
            f'<div style="background:#111318;border:1px solid #252830;border-radius:10px;'
            f'padding:16px;margin-bottom:12px;">'

            # card header row
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">'
            f'  <div>'
            f'    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
            f'      <span style="font-size:12px;color:#f1f5f9;font-weight:700;">{inc_id}</span>'
            f'      <span style="background:#1e293b;color:{sev_c};border:1px solid {sev_c}44;'
            f'border-radius:4px;padding:1px 6px;font-size:10px;font-weight:700;">{sev}</span>'
            f'      <span style="background:#1e293b;color:#94a3b8;border:1px solid #334155;'
            f'border-radius:4px;padding:1px 6px;font-size:10px;">{cat}</span>'
            f'    </div>'
            + _match_badge(exact_m, gt_id) +
            f'  </div>'
            f'  <div style="font-size:32px;font-weight:700;color:{oc};'
            f'font-family:\'Syne\',sans-serif;line-height:1;text-align:right;">'
            f'    {overall}<span style="font-size:13px;color:#475569;">/100</span>'
            f'  </div>'
            f'</div>'
        )

        # Axis rows
        for ax, (icon, label) in AXIS_LABELS.items():
            ax_data  = axes.get(ax, {})
            ax_score = ax_data.get("score", 0)
            ax_ratio = ax_data.get("rationale", "")
            html.append(
                f'<div style="margin-bottom:8px;">'
                f'  <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;">'
                f'    <span style="font-size:12px;width:20px;">{icon}</span>'
                f'    <span style="font-size:11px;color:#94a3b8;flex:1;">{label}</span>'
                f'    <span style="font-size:12px;font-weight:700;color:{_score_color(ax_score*10)};'
                f'      width:22px;text-align:right;">{ax_score}</span>'
                f'    <span style="font-size:11px;color:#475569;">/10</span>'
                f'  </div>'
                f'  <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;">'
                f'    <div style="width:20px;"></div>'
                + _axis_bar(ax_score) +
                f'  </div>'
                f'  <div style="font-size:11px;color:#64748b;padding-left:28px;">{ax_ratio}</div>'
                f'</div>'
            )

        # Verdict
        if verdict:
            html.append(
                f'<div style="margin-top:10px;padding:10px 12px;background:#0f172a;'
                f'border-left:3px solid #a78bfa;border-radius:0 6px 6px 0;">'
                f'<div style="font-size:10px;font-weight:700;color:#a78bfa;letter-spacing:1px;'
                f'text-transform:uppercase;margin-bottom:4px;">Judge Verdict</div>'
                f'<div style="font-size:12px;color:#94a3b8;line-height:1.6;">{verdict}</div>'
                f'</div>'
            )

        html.append('</div>')  # close card

    html.append('</div>')
    return "\n".join(html)

# ─────────────────────────────────────────────────────────────
# Core generator
# ─────────────────────────────────────────────────────────────
def process_logs(files, demo_mode):
    if not files and not demo_mode:
        yield _progress_html(1, "❌ Please upload at least one log file."), "{}", "", None, None, _n8n_empty(), _eval_empty()
        return

    for step in range(1, 8):
        yield _progress_html(step), "{}", "", None, None, _n8n_empty(), _eval_empty()

    try:
        file_paths = [f.name for f in files] if files else []
        response   = analyze_uploaded_logs(file_paths)

        incidents_raw = response.get("incidents", [])
        incidents     = [IncidentResult(**i) for i in incidents_raw]
        md_report     = response_to_markdown(incidents, response["summary"])

        # Step 8: n8n
        yield (_progress_html(8, "🚀 Dispatching to Slack + JIRA via n8n…"),
               json.dumps(response), md_report, None, None,
               '<div style="color:#f59e0b;padding:20px;font-family:\'JetBrains Mono\',monospace;font-size:12px;">▶ Sending to n8n…</div>',
               _eval_empty())

        n8n_results = notify_all_incidents(incidents_raw)
        n8n_html    = _n8n_html(n8n_results)

        # Step 9: LLM judge
        yield (_progress_html(9, "🧪 Running LLM-as-Judge (OpenRouter)…"),
               json.dumps(response), md_report, None, None, n8n_html,
               '<div style="color:#a78bfa;padding:20px;font-family:\'JetBrains Mono\',monospace;font-size:12px;">▶ Calling OpenRouter judge…</div>')

        # Pass None → evaluator uses DEFAULT_GROUND_TRUTH (covers all categories)
        eval_result = evaluate_all(incidents_raw, ground_truth=None)
        eval_html   = _eval_html(eval_result)

        # Step 10: export
        tmp    = tempfile.gettempdir()
        run_id = response["run_id"]
        json_file = os.path.join(tmp, f"analysis_{run_id}.json")
        md_file   = os.path.join(tmp, f"report_{run_id}.md")
        eval_file = os.path.join(tmp, f"eval_{run_id}.json")

        with open(json_file, "w") as f: json.dump(response,    f, indent=2)
        with open(md_file,   "w") as f: f.write(md_report)
        with open(eval_file, "w") as f: json.dump(eval_result, f, indent=2)

        yield (
            _progress_html(10, "✅ Complete — analysis, n8n & eval done!"),
            json.dumps(response, indent=2),
            md_report,
            json_file,
            md_file,
            n8n_html,
            eval_html,
        )

    except Exception as e:
        yield (_progress_html(8, f"❌ Error: {e}"),
               "{}", f"### Error\n```\n{e}\n```",
               None, None, _n8n_empty(), _eval_empty())

# ─────────────────────────────────────────────────────────────
# App builder
# ─────────────────────────────────────────────────────────────
def build_app():
    with gr.Blocks(css=CUSTOM_CSS, theme=gr.themes.Base()) as demo:

        gr.HTML(f"""
        <div class="iq-header">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
            <span style="font-size:28px;">🚨</span>
            <h1 class="iq-title">{APP_TITLE}</h1>
            <span class="iq-badge">v3.1</span>
          </div>
          <p class="iq-sub">{APP_SUBTITLE}</p>
        </div>
        """)

        gr.HTML(STRATEGY_HTML)

        with gr.Row(equal_height=False):

            with gr.Column(scale=1, min_width=320):
                log_files     = gr.File(file_count="multiple",
                                        label="Upload Logs (.log .txt .zip .jsonl)")
                demo_checkbox = gr.Checkbox(label="Demo Mode (no files needed)", value=False)
                analyze_btn   = gr.Button("⚡ Run Analysis  →  notify",
                                          variant="primary", elem_classes=["run-btn"])
                gr.HTML(PIPELINE_HTML)
                progress_area = gr.HTML(_progress_html(0))

            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.TabItem("📊 Analysis Report"):
                        report_output = gr.Markdown(
                            "Upload log files and click **Run Analysis** to begin.",
                            elem_classes=["prose-report"],
                        )
                    with gr.TabItem("📄 Raw JSON"):
                        json_output = gr.Code(language="json", label="")
                    with gr.TabItem("🚀 notifications"):
                        n8n_output  = gr.HTML(_n8n_empty())
                    with gr.TabItem("🧪 LLM-as-Judge Evals"):
                        eval_output = gr.HTML(_eval_empty())

                with gr.Row():
                    download_json = gr.File(label="📥 Download JSON")
                    download_md   = gr.File(label="📥 Download Report")

        analyze_btn.click(
            fn=process_logs,
            inputs=[log_files, demo_checkbox],
            outputs=[progress_area, json_output, report_output,
                     download_json, download_md, n8n_output, eval_output],
        )

    return demo


if __name__ == "__main__":
    build_app().launch(server_name="0.0.0.0", server_port=7860)