from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Iterable, Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


@dataclass(frozen=True)
class Story:
    owner: str
    title: str
    story: str
    files: Sequence[str]
    steps: Sequence[str]
    acceptance: Sequence[str]
    dependencies: Sequence[str]


def styles():
    base = getSampleStyleSheet()
    base.add(
        ParagraphStyle(
            "CoverTitle",
            parent=base["Title"],
            fontSize=25,
            leading=31,
            alignment=TA_CENTER,
            spaceAfter=18,
            textColor=colors.HexColor("#172033"),
        )
    )
    base.add(
        ParagraphStyle(
            "CoverSub",
            parent=base["BodyText"],
            fontSize=12,
            leading=17,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#445066"),
            spaceAfter=18,
        )
    )
    base.add(
        ParagraphStyle(
            "H1x",
            parent=base["Heading1"],
            fontSize=17,
            leading=22,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor("#21304d"),
        )
    )
    base.add(
        ParagraphStyle(
            "H2x",
            parent=base["Heading2"],
            fontSize=13,
            leading=17,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor("#284b63"),
        )
    )
    base.add(
        ParagraphStyle(
            "Bodyx",
            parent=base["BodyText"],
            fontSize=9.7,
            leading=13.5,
            alignment=TA_LEFT,
            spaceAfter=6,
        )
    )
    base.add(
        ParagraphStyle(
            "Smallx",
            parent=base["BodyText"],
            fontSize=8.2,
            leading=11,
            textColor=colors.HexColor("#404a5a"),
        )
    )
    base.add(
        ParagraphStyle(
            "TableHead",
            parent=base["BodyText"],
            fontSize=8.8,
            leading=11,
            textColor=colors.white,
            alignment=TA_CENTER,
        )
    )
    base.add(
        ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontSize=8,
            leading=10.5,
        )
    )
    return base


S = styles()


def p(text: str, style: str = "Bodyx") -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>"), S[style])


def bullets(items: Iterable[str], level: int = 0) -> ListFlowable:
    return ListFlowable(
        [ListItem(p(item), leftIndent=8) for item in items],
        bulletType="bullet",
        start=None,
        leftIndent=18 + level * 12,
        bulletFontSize=7,
        bulletOffsetY=1,
    )


def numbered(items: Iterable[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(p(item), leftIndent=10) for item in items],
        bulletType="1",
        leftIndent=18,
        bulletFontSize=8,
    )


def code_block(text: str) -> Preformatted:
    return Preformatted(text, S["Code"])


def table(headers: Sequence[str], rows: Sequence[Sequence[str]], widths: Sequence[float]) -> Table:
    data = [[p(h, "TableHead") for h in headers]]
    data.extend([[p(str(cell), "TableCell") for cell in row] for row in rows])
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#26364f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b8c0cc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#fbfcfe")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fb")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6a7280"))
    canvas.drawString(0.55 * inch, 0.38 * inch, "IncidentIQ Hackathon Plan")
    canvas.drawRightString(7.72 * inch, 0.38 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(path: Path, story: list):
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.65 * inch,
        title=path.stem,
        author="IncidentIQ Team",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


ARCHITECTURE_ROWS = [
    (
        "Input",
        "Gradio manual upload plus n8n-triggered automated log sources.",
        "User uploads logs; optional Datadog/S3/Email trigger calls n8n webhook.",
    ),
    (
        "Processing",
        "FastAPI exposes the backend; LangGraph manages agent state and routing.",
        "Parser/classifier, timeline, RCA, remediation, critic, notification, ticket, cookbook.",
    ),
    (
        "RAG Engine",
        "Runbook/SOP retrieval enriches remediation and RCA.",
        "Lexical/local fallback first; OpenAI embeddings + Weaviate/FAISS optional.",
    ),
    (
        "Integrations",
        "n8n switch routes high severity incidents to Slack/JIRA.",
        "Preview-first payloads; real writes only when credentials and approval are present.",
    ),
    (
        "Output",
        "Traceable, actionable incident summary.",
        "Markdown/JSON/CSV reports, Slack message, JIRA ticket payload, cookbook checklist.",
    ),
]


STORIES = [
    Story(
        owner="Person 1 - n8n Workflow Owner",
        title="Automated workflow routing and integration orchestration",
        story="As a DevOps/SRE user, I want n8n to receive incidents and route critical issues to Slack/JIRA so that the demo proves real workflow automation.",
        files=("workflows/n8n_incidentiq_workflow.json", "docs/n8n_setup.md"),
        steps=(
            "Create a Webhook Trigger that accepts a log analysis request or a completed analysis payload.",
            "Add an HTTP Request node that calls FastAPI POST /analyze with sample logs or a staged file reference.",
            "Add a Switch node using highest_severity with branches for P1/P2, P3, and Unknown.",
            "Route P1/P2 to Slack and JIRA nodes; route P3 to Slack/report only; route Unknown to report-only.",
            "Add HTTP Response node returning run_id, status, highest_severity, report links, and payload previews.",
            "Export the workflow JSON and add a short import/run guide.",
            "Capture screenshots of successful n8n execution for README/demo.",
        ),
        acceptance=(
            "n8n can call the hosted or local FastAPI /analyze endpoint.",
            "P1/P2 route reaches Slack/JIRA branch; P3/Unknown does not create JIRA.",
            "Workflow JSON is committed and documented.",
            "Demo can show n8n execution history in under 45 seconds.",
        ),
        dependencies=("FastAPI /analyze contract", "sample payloads", "optional Slack/JIRA credentials"),
    ),
    Story(
        owner="Person 2 - Gradio Frontend Owner",
        title="Interactive incident dashboard",
        story="As a judge, I want a public dashboard where I can upload logs and inspect the final analysis without installing anything.",
        files=("src/ui/gradio_app.py", "app.py"),
        steps=(
            "Build Gradio Blocks UI with file upload, run button, status trace, and result tabs.",
            "Support .zip, .jsonl, .log, and .txt upload.",
            "Call FastAPI /analyze or a shared local pipeline function depending on deployment mode.",
            "Render incident table with severity, category, affected service, confidence, and evidence count.",
            "Render detail tabs for timeline, RCA, remediation, cookbook, Slack preview, JIRA preview, and raw JSON.",
            "Add download buttons for Markdown and JSON report artifacts.",
            "Make the UI usable without API keys by displaying deterministic fallback results.",
        ),
        acceptance=(
            "Public URL opens and accepts sample logs.",
            "The dashboard shows at least one complete incident from provided datasets.",
            "Slack/JIRA previews are visible in the UI.",
            "Judges can download or copy final report JSON/Markdown.",
        ),
        dependencies=("FastAPI endpoint or pipeline runner", "shared response schema", "sample datasets"),
    ),
    Story(
        owner="Person 3 - FastAPI Backend Owner",
        title="Stable backend API for Gradio and n8n",
        story="As frontend and automation clients, Gradio and n8n need a reliable HTTP API that accepts logs and returns standardized incident intelligence.",
        files=("src/api/main.py", "src/api/schemas.py", "Dockerfile", ".env.example"),
        steps=(
            "Create FastAPI app with GET /health, POST /analyze, GET /runs/{run_id}, and GET /reports/{run_id}.",
            "Define Pydantic request and response models matching the shared output contract.",
            "Accept multipart file uploads and JSON requests with staged file paths.",
            "Call the LangGraph/pipeline runner and persist outputs under outputs/{run_id}.",
            "Return consistent JSON even if LLM, RAG, Slack, or JIRA is unavailable.",
            "Enable CORS for Gradio and n8n.",
            "Add Docker or Hugging Face/Render entrypoint.",
        ),
        acceptance=(
            "GET /health returns ok.",
            "POST /analyze works with block1 sample data.",
            "Gradio and n8n can consume the same response shape.",
            "No API key is required for deterministic demo mode.",
        ),
        dependencies=("pipeline runner", "models", "output contract"),
    ),
    Story(
        owner="Person 4 - RAG Owner",
        title="Runbook/SOP retrieval for grounded remediation",
        story="As a remediation agent, I need relevant SOP and prior-incident context so that recommended actions look credible and traceable.",
        files=("runbooks/*.md", "src/rag/runbook_store.py", "src/rag/retriever.py", "src/rag/vector_store.py"),
        steps=(
            "Create mock SOP markdown files for database, timeout, auth, memory, queue, disk, dependency, and deployment incidents.",
            "Implement a RunbookStore that loads and chunks local markdown documents.",
            "Implement lexical retrieval using category, service, error terms, and signal keywords.",
            "Return top three chunks with title, source, score, and excerpt.",
            "Add optional OpenAI embedding path if OPENAI_API_KEY is present.",
            "Add optional FAISS/Weaviate adapter only after lexical fallback is stable.",
            "Expose retrieved context to RCA and remediation agents.",
        ),
        acceptance=(
            "Known incident categories retrieve relevant SOP content.",
            "Pipeline still works if embeddings/vector DB are unavailable.",
            "Final output lists retrieved runbook context.",
            "README explains current fallback and target Weaviate architecture.",
        ),
        dependencies=("incident category/service/evidence fields", "mock SOP content"),
    ),
    Story(
        owner="Person 5 - Agent Owner A",
        title="Ingestion, signal extraction, classification, and timeline",
        story="As the analysis system, I need to convert noisy logs into structured evidence and incident candidates for downstream reasoning.",
        files=("src/models/*.py", "src/ingest/*.py", "src/signals/*.py", "src/clustering/*.py", "src/agents/classifier_agent.py", "src/agents/timeline_agent.py"),
        steps=(
            "Extract v4 notebook models for LogEvent, SignalEvidence, EvidenceCluster, IncidentAnalysisResult, and TimelineEvent.",
            "Implement safe file loading, ZIP extraction, log discovery, parsing, and normalization.",
            "Implement deterministic regex/signal rules for database, network, auth, memory, timeout, queue, disk, deployment, and dependency failures.",
            "Implement clustering by file, category, service, time bucket, and signature where available.",
            "Implement classifier agent with severity/category fallback heuristics.",
            "Implement timeline agent by sorting cited evidence and selecting representative events.",
            "Ensure every evidence item has source_file and line_no.",
        ),
        acceptance=(
            "Sample logs produce structured events and signal evidence.",
            "At least four incident categories are detected reliably.",
            "Incidents include severity, category, evidence references, and timeline.",
            "Runtime pipeline never reads ground_truth_eval_only.",
        ),
        dependencies=("v4 notebook implementation", "sample datasets"),
    ),
    Story(
        owner="Person 6 - Agent Owner B",
        title="RCA, remediation, critic, notification, ticket, and cookbook agents",
        story="As the incident response team, I want evidence-backed recommendations and action-ready outputs that are useful but safe.",
        files=("src/agents/rca_agent.py", "src/agents/remediation_agent.py", "src/agents/critic_agent.py", "src/agents/notification_agent.py", "src/agents/ticket_agent.py", "src/agents/cookbook_agent.py", "src/reporting/*.py"),
        steps=(
            "Implement RCA agent with probable cause, supporting evidence, missing evidence, confidence, and summary.",
            "Implement remediation agent with immediate actions, validation checks, rollback notes, and risk level.",
            "Implement critic agent that flags unsupported claims, missing evidence, and unsafe actions.",
            "Implement notification agent that returns Slack Block Kit-style JSON and plain text fallback.",
            "Implement ticket agent that returns JIRA-compatible payloads for P1/P2 only by default.",
            "Implement cookbook synthesizer that creates detection, triage, remediation, validation, and prevention checklists.",
            "Add deterministic fallback output for every agent if LLM calls fail.",
        ),
        acceptance=(
            "Each agent returns structured Pydantic output.",
            "RCA and remediation cite evidence and/or retrieved runbook context.",
            "P1/P2 incidents generate Slack and JIRA payloads; P3 skips JIRA by default.",
            "Agent failures degrade gracefully and do not crash the run.",
        ),
        dependencies=("clusters and classifier output", "RAG context", "shared response schema"),
    ),
    Story(
        owner="Person 7 - Integration, QA, Deployment, README, Demo Owner",
        title="Submission readiness and end-to-end polish",
        story="As the team, we need one owner ensuring the full project runs publicly, is documented, and can be judged quickly.",
        files=("README.md", "docs/demo_script.md", "docs/screenshots/*", "tests/*", "requirements.txt"),
        steps=(
            "Own final merge/integration and keep everyone aligned to the shared JSON contract.",
            "Add README setup instructions for local, hosted, Gradio, FastAPI, and n8n usage.",
            "Add architecture section using the final uploaded diagram as the source of truth.",
            "Add scoring section mapping concepts, difficulty, and code quality to judge criteria.",
            "Create smoke tests for ingest, pipeline, API health, and sample analysis.",
            "Deploy the public demo and verify from a clean browser session.",
            "Record a strict under-5-minute demo video and collect screenshots.",
        ),
        acceptance=(
            "Public URL works.",
            "Fresh clone can run deterministic demo.",
            "README has exact commands and sample flow.",
            "Submission includes repo, hosted URL, n8n workflow export, and demo video.",
        ),
        dependencies=("all team outputs", "hosting account", "sample datasets"),
    ),
]


def implementation_plan_story() -> list:
    story = []
    story += [
        p("IncidentIQ", "CoverTitle"),
        p("Hackathon Implementation Plan", "CoverTitle"),
        p(
            "Multi-agent DevOps Incident Analysis Suite using Gradio, FastAPI, LangGraph, n8n workflow automation, and RAG.",
            "CoverSub",
        ),
        Spacer(1, 0.25 * inch),
        p("Purpose", "H1x"),
        p(
            "This document converts the final architecture diagram into an implementation plan optimized for a seven-person hackathon team submitting tomorrow. The plan favors a working, hosted, judge-friendly demo over production completeness.",
        ),
        p("Final Architecture Mapping", "H1x"),
        table(
            ["Architecture Area", "Implementation Choice", "Hackathon Behavior"],
            ARCHITECTURE_ROWS,
            [1.2 * inch, 2.2 * inch, 3.65 * inch],
        ),
        p("Current Repository State", "H1x"),
        bullets(
            [
                "The src/ directory has the intended module folders but no production implementation yet.",
                "The latest usable implementation is the SRC-aligned v4 notebook, which should be extracted into src/ modules.",
                "Existing docs already define scoring priorities: concept score, difficulty, and code quality.",
                "The final uploaded diagram supersedes older frontend assumptions: Gradio is the frontend and n8n is the workflow/integration orchestrator.",
            ]
        ),
        p("Shared System Contract", "H1x"),
        p(
            "Every teammate should build toward the same response object so Gradio, FastAPI, n8n, agents, reporting, and RAG can work in parallel."
        ),
        code_block(
            """{
  "run_id": "string",
  "status": "completed|failed|needs_approval",
  "highest_severity": "P1|P2|P3|Unknown",
  "incidents": [],
  "slack_payloads": [],
  "jira_payloads": [],
  "cookbooks": [],
  "reports": {
    "markdown": "path",
    "json": "path",
    "csv": "path"
  },
  "eval": {
    "enabled": false,
    "summary": null
  }
}"""
        ),
        p("MVP Scope", "H1x"),
        bullets(
            [
                "Gradio public upload dashboard.",
                "FastAPI /health and /analyze endpoints.",
                "Deterministic log parsing, signal extraction, clustering, and fallback reasoning.",
                "LangGraph-style multi-agent orchestration.",
                "RAG context from local SOP/runbook documents.",
                "Slack and JIRA preview payloads, optionally sent by n8n.",
                "n8n workflow export showing severity-based routing.",
                "Markdown/JSON/CSV report outputs.",
                "README, setup commands, screenshots, and under-5-minute demo video.",
            ]
        ),
        p("Deliberate De-scope", "H1x"),
        bullets(
            [
                "Do not block submission on real Slack/JIRA credentials; preview payloads are acceptable.",
                "Do not block submission on Weaviate; lexical/local RAG is sufficient for MVP.",
                "Do not require LLM API keys for the demo; deterministic fallback must work.",
                "Do not build full FastAPI plus separate database persistence; file-based outputs are enough.",
                "Do not add large zip-only artifacts to GitHub; commit source code and small sample data references.",
            ]
        ),
        PageBreak(),
        p("Implementation Phases", "H1x"),
        table(
            ["Phase", "Timebox", "Outcome"],
            [
                ("0. Freeze", "0-1 hour", "Lock architecture, branches, output contract, and sample dataset."),
                ("1. Core", "1-4 hours", "Extract v4 notebook logic into src/ and get deterministic pipeline working."),
                ("2. Agents + RAG", "2-6 hours", "Add LangGraph runner, agent outputs, and runbook retrieval."),
                ("3. Interfaces", "3-7 hours", "Wire FastAPI, Gradio, and n8n to the same response schema."),
                ("4. Hosting", "6-8 hours", "Deploy Gradio/FastAPI and import n8n workflow."),
                ("5. Polish", "8-10 hours", "README, screenshots, demo script, smoke tests, final video."),
                ("6. Freeze", "Final hour", "Only fix blockers; submit repo, URL, workflow export, and video."),
            ],
            [1.3 * inch, 1.15 * inch, 4.6 * inch],
        ),
        p("Hosting Recommendation", "H1x"),
        bullets(
            [
                "Use Hugging Face Spaces with Docker for the public Gradio demo if possible.",
                "Run FastAPI in the same container or expose it via Render free tier if splitting services.",
                "Use n8n Cloud trial/free workspace for the workflow and export the workflow JSON.",
                "Keep secrets optional through .env.example and feature flags.",
            ]
        ),
        p("Critical Environment Flags", "H1x"),
        code_block(
            """ENABLE_LLM_MODE=false
ENABLE_RAG_MODE=true
ENABLE_PREVIEW_MODE=true
ENABLE_REAL_INTEGRATIONS=false
OPENAI_API_KEY=
OPENAI_BASE_URL=
MODEL_NAME=
SLACK_WEBHOOK_URL=
JIRA_BASE_URL=
JIRA_EMAIL=
JIRA_API_TOKEN="""
        ),
        p("Definition of Done", "H1x"),
        bullets(
            [
                "A judge can open a public URL, upload a sample log file, and see incidents plus RCA/remediation outputs.",
                "The demo visibly uses multiple agents, RAG context, and n8n routing.",
                "The project runs without paid services or API keys using fallback mode.",
                "The README explains setup, architecture, concepts used, and judging value.",
                "The demo video is under five minutes.",
            ]
        ),
    ]
    return story


def user_stories_story() -> list:
    story = []
    story += [
        p("IncidentIQ", "CoverTitle"),
        p("Seven-Person User Stories and Sprint Execution Plan", "CoverTitle"),
        p(
            "Detailed owner-by-owner work breakdown for completing the hackathon submission by tomorrow.",
            "CoverSub",
        ),
        p("Team Plan Overview", "H1x"),
        table(
            ["Owner", "Primary Deliverable", "Integration Point"],
            [
                ("Person 1", "n8n workflow", "Calls FastAPI and routes Slack/JIRA branches."),
                ("Person 2", "Gradio dashboard", "Calls FastAPI or pipeline runner."),
                ("Person 3", "FastAPI backend", "Shared API for Gradio and n8n."),
                ("Person 4", "RAG engine", "Supplies context to RCA/remediation agents."),
                ("Person 5", "Parser/classifier/timeline agents", "Feeds structured evidence into graph."),
                ("Person 6", "RCA/remediation/action agents", "Produces final incident intelligence."),
                ("Person 7", "Integration, QA, deployment, README, demo", "Keeps submission coherent and hosted."),
            ],
            [1.0 * inch, 2.55 * inch, 3.5 * inch],
        ),
        p("Parallel Work Rule", "H1x"),
        p(
            "Everyone should code against the shared response contract. If a dependency is not ready, use a stub returning the same shape. This avoids blocking the team while preserving integration safety.",
        ),
        PageBreak(),
    ]
    for s in STORIES:
        story += [
            p(s.owner, "H1x"),
            p(s.title, "H2x"),
            p(s.story),
            p("Owned Files / Artifacts", "H2x"),
            bullets(s.files),
            p("Detailed Steps", "H2x"),
            numbered(s.steps),
            p("Acceptance Criteria", "H2x"),
            bullets(s.acceptance),
            p("Dependencies", "H2x"),
            bullets(s.dependencies),
            Spacer(1, 0.12 * inch),
        ]
    story += [
        PageBreak(),
        p("Final Submission Checklist", "H1x"),
        bullets(
            [
                "Public hosted Gradio URL works from a clean browser.",
                "FastAPI /health and /analyze work locally or on hosted backend.",
                "n8n workflow JSON is committed and importable.",
                "Sample logs are available and documented.",
                "README includes setup instructions, architecture, concepts used, and scoring alignment.",
                "Screenshots show Gradio, n8n, Slack/JIRA preview, and final report.",
                "Demo video is less than five minutes.",
                "No hidden ground-truth files are read during runtime analysis.",
                "Repo contains actual code, not only notebooks or zip files.",
            ]
        ),
        p("Demo Script", "H1x"),
        numbered(
            [
                "Open the public Gradio app and upload the easy sample incident logs.",
                "Show the status trace moving through ingest, signals, clustering, agents, RAG, and reports.",
                "Open the top incident and explain severity, evidence references, timeline, and RCA.",
                "Show retrieved SOP/runbook context and remediation checklist.",
                "Show Slack and JIRA previews; then show n8n severity switch routing.",
                "Download or open the final Markdown/JSON report.",
                "Close by mapping the project to judging criteria: concepts, difficulty, and code quality.",
            ]
        ),
    ]
    return story


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    build_pdf(DOCS / "IncidentIQ_Hackathon_Implementation_Plan.pdf", implementation_plan_story())
    build_pdf(DOCS / "IncidentIQ_Team_User_Stories_Sprint_Plan.pdf", user_stories_story())
    print("Generated:")
    print(DOCS / "IncidentIQ_Hackathon_Implementation_Plan.pdf")
    print(DOCS / "IncidentIQ_Team_User_Stories_Sprint_Plan.pdf")


if __name__ == "__main__":
    main()
