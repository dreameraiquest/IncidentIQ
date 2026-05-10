#!/usr/bin/env python3
"""
Generate a comprehensive PDF guide for IncidentIQ Notebooks
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Image, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime

# Setup
output_path = "IncidentIQ_Notebooks_Detailed_Guide.pdf"
doc = SimpleDocTemplate(output_path, pagesize=letter,
                       rightMargin=0.75*inch, leftMargin=0.75*inch,
                       topMargin=0.75*inch, bottomMargin=0.75*inch)

styles = getSampleStyleSheet()
story = []

# Custom styles
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor=colors.HexColor('#1a1a1a'),
    spaceAfter=20,
    alignment=TA_CENTER,
    fontName='Helvetica-Bold'
)

heading1_style = ParagraphStyle(
    'CustomHeading1',
    parent=styles['Heading1'],
    fontSize=14,
    textColor=colors.HexColor('#1a3a7a'),
    spaceAfter=12,
    spaceBefore=12,
    fontName='Helvetica-Bold'
)

heading2_style = ParagraphStyle(
    'CustomHeading2',
    parent=styles['Heading2'],
    fontSize=12,
    textColor=colors.HexColor('#2a4a9a'),
    spaceAfter=10,
    spaceBefore=10,
    fontName='Helvetica-Bold'
)

normal_style = ParagraphStyle(
    'CustomNormal',
    parent=styles['Normal'],
    fontSize=10,
    spaceAfter=10,
    alignment=TA_LEFT
)

code_style = ParagraphStyle(
    'Code',
    parent=styles['Normal'],
    fontSize=8,
    fontName='Courier',
    textColor=colors.HexColor('#333333'),
    backColor=colors.HexColor('#f5f5f5'),
    spaceAfter=8
)

# Title Page
story.append(Paragraph("IncidentIQ", title_style))
story.append(Paragraph("Notebooks Detailed Guide", heading1_style))
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph(
    "Multi-Agent AI Platform for DevOps Incident Detection, RCA & Automated Response",
    ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12,
                   alignment=TA_CENTER, textColor=colors.HexColor('#666666'))
))
story.append(Spacer(1, 0.5*inch))
story.append(Paragraph(
    f"Generated: {datetime.now().strftime('%B %d, %Y')}",
    ParagraphStyle('Date', parent=styles['Normal'], fontSize=10,
                   alignment=TA_CENTER, textColor=colors.HexColor('#999999'))
))
story.append(PageBreak())

# Table of Contents
story.append(Paragraph("Table of Contents", heading1_style))
story.append(Spacer(1, 0.2*inch))
toc_items = [
    "1. Overview of All Notebooks",
    "2. Notebook 1: Original MVP (v1)",
    "3. Notebook 2: LangGraph + LLM (v2)",
    "4. Notebook 3: src/ Architecture Aligned (v3)",
    "5. Notebook 4: Production-Ready (v4)",
    "6. Detailed Feature Breakdown",
    "7. Data Flow Across Notebooks",
    "8. How to Use These Notebooks",
    "9. Key Takeaway"
]
for item in toc_items:
    story.append(Paragraph(item, normal_style))
story.append(PageBreak())

# Section 1: Overview
story.append(Paragraph("1. Overview of All Notebooks", heading1_style))
story.append(Spacer(1, 0.1*inch))

overview_text = """
There are 4 progressively refined notebooks that demonstrate the IncidentIQ system,
moving from proof-of-concept to production-aligned code. Each notebook builds upon the
previous one, introducing new concepts and refining implementations.
"""
story.append(Paragraph(overview_text, normal_style))
story.append(Spacer(1, 0.15*inch))

# Notebook comparison table
notebook_data = [
    ['Notebook', 'File Size', 'Purpose', 'Status', 'Focus'],
    ['v1: Original MVP', '288 KB', 'Foundation & Concepts', 'First Generation', 'Agent fundamentals'],
    ['v2: LangGraph', '50 KB', 'Graph Orchestration', 'Second Generation', 'LLM + state mgmt'],
    ['v3: src/ Aligned', '99 KB', 'Architecture Validation', 'Third Generation', 'Modular structure'],
    ['v4: Production', '111 KB', 'Final Polished', 'Latest (RECOMMENDED)', 'Best practices']
]

notebook_table = Table(notebook_data, colWidths=[1.2*inch, 0.9*inch, 1.3*inch, 1.1*inch, 1.4*inch])
notebook_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a7a')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('FONTSIZE', (0, 1), (-1, -1), 8),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
]))
story.append(notebook_table)
story.append(PageBreak())

# Section 2: Notebook v1
story.append(Paragraph("2. Multi_Agent_DevOps_Incident_Analysis_Suite_Colab.ipynb", heading1_style))
story.append(Paragraph("(288 KB) — Original MVP / Proof-of-Concept", heading2_style))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("<b>Purpose:</b> First generation implementation; foundation for later versions", normal_style))
story.append(Paragraph("<b>Status:</b> MVP, notebook-first approach", normal_style))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("Key Demonstrations:", heading2_style))
v1_features = [
    "• End-to-end incident analysis pipeline using 9 specialized agents",
    "• Raw Colab implementation without LangGraph orchestration",
    "• Sequential agent workflow (Parser → Signal → Classify → RCA → Timeline → Reporting)",
    "• Simple deterministic scoring without LLM reasoning",
    "• Useful for prototyping and learning core concepts"
]
for feature in v1_features:
    story.append(Paragraph(feature, normal_style))

story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("The 9 Agents:", heading2_style))

v1_agents_data = [
    ['Agent', 'Responsibility'],
    ['Parser', 'Normalize raw log lines into structured events'],
    ['Signal Extraction', 'Detect operational signals using regex patterns'],
    ['Classifier', 'Infer incident category (Database, Network, Auth, etc.)'],
    ['RCA', 'Perform root cause analysis with supporting evidence'],
    ['Timeline', 'Reconstruct incident chronology from events'],
    ['Notification', 'Generate Slack/Teams-style alert previews'],
    ['Ticket', 'Generate JIRA/GitHub-style ticket previews'],
    ['Cookbook', 'Create reusable runbook/checklist items'],
    ['Eval/Scoring', 'Compare results against hidden ground truth']
]

agents_table = Table(v1_agents_data, colWidths=[2*inch, 4*inch])
agents_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a7a')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('FONTSIZE', (0, 1), (-1, -1), 8),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
]))
story.append(agents_table)

story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("Workflow:", heading2_style))
workflow_text = """
1. User uploads raw log files (.log, .txt, .jsonl, .zip)<br/>
2. Parser normalizes them into structured LogEvent objects<br/>
3. Signal extractor finds operational anomalies using pattern matching<br/>
4. Classifier + RCA agents reason over evidence<br/>
5. Timeline agent builds incident narrative<br/>
6. Agents generate preview notifications and tickets<br/>
7. Eval module compares results to ground truth
"""
story.append(Paragraph(workflow_text, normal_style))
story.append(PageBreak())

# Section 3: Notebook v2
story.append(Paragraph("3. Multi_Agent_DevOps_Incident_Analysis_Suite_LangGraph_Colab_v2.ipynb", heading1_style))
story.append(Paragraph("(50 KB) — LangGraph + LLM Integration", heading2_style))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("<b>Purpose:</b> Second generation; introduces graph orchestration and LLM reasoning", normal_style))
story.append(Paragraph("<b>Status:</b> Adds structured state management and API integration", normal_style))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("What It Adds:", heading2_style))
v2_additions = [
    "• <b>LangGraph Integration</b> — Replaces simple sequential calls with a proper workflow graph",
    "• <b>LLM Reasoning Layer</b> — Moves ambiguous logic to Claude/GPT instead of heuristics only",
    "• <b>Dual-Mode Operation</b> — No-key mode (deterministic) + LLM mode (enhanced reasoning)",
    "• <b>State Management</b> — IncidentGraphState object passed between graph nodes",
    "• <b>Conditional Routing</b> — Retry loops, fallback paths, critic feedback"
]
for addition in v2_additions:
    story.append(Paragraph(addition, normal_style))

story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("Key Sections:", heading2_style))

v2_sections_data = [
    ['Section', 'Focus'],
    ['LLM Configuration', 'API key setup, model selection, fallback mode'],
    ['Upload Logs', 'Colab file picker integration'],
    ['Schemas', 'Pydantic models for state passing'],
    ['Signal Extraction & Clustering', 'Rules-based anomaly detection + grouping'],
    ['RAG Library', 'Embedded runbook retrieval (lexical search)'],
    ['LangGraph Agents', 'Agents that reason with LLMs'],
    ['Run Pipeline', 'Execute the LangGraph workflow'],
    ['Eval & Scoring', 'Compare results to ground truth']
]

v2_table = Table(v2_sections_data, colWidths=[2*inch, 4*inch])
v2_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a7a')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('FONTSIZE', (0, 1), (-1, -1), 8),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
]))
story.append(v2_table)

story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("Key Improvements:", heading2_style))
improvements = [
    "• Introduces IncidentGraphState (shared state object)",
    "• Agents are now LangGraph nodes that transform state",
    "• Explicit state passing between agents",
    "• LLM-driven reasoning for ambiguous cases",
    "• Critic agent validates conclusions to reduce hallucinations"
]
for improvement in improvements:
    story.append(Paragraph(improvement, normal_style))

story.append(PageBreak())

# Section 4: Notebook v3
story.append(Paragraph("4. Multi_Agent_DevOps_Incident_Analysis_Suite_SRC_Aligned_Colab_v3.ipynb", heading1_style))
story.append(Paragraph("(99 KB) — src/ Architecture Aligned", heading2_style))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("<b>Purpose:</b> Third generation; aligns notebook structure with production code organization", normal_style))
story.append(Paragraph("<b>Key Innovation:</b> Single comprehensive notebook where each section maps directly to a src/ folder module", normal_style))
story.append(Spacer(1, 0.15*inch))

story.append(Paragraph("Section-by-Section Mapping to src/:", heading2_style))

mapping_data = [
    ['Notebook Section', 'src/ Folder', 'Purpose'],
    ['config/', 'src/config/', 'Settings, feature flags, LLM API config'],
    ['models/', 'src/models/', 'Pydantic enums, LogEvent, Cluster, Incident'],
    ['utils/', 'src/utils/', 'Hash, timestamps, paths, text utilities'],
    ['ingest/', 'src/ingest/', 'ZIP loader, log parser, normalizer'],
    ['signals/', 'src/signals/', 'SignalRule engine, pattern matching'],
    ['clustering/', 'src/clustering/', 'EvidenceClusterer, hybrid strategies'],
    ['rag/', 'src/rag/', 'RunbookStore, lexical retriever'],
    ['agents/', 'src/agents/', 'LLM agents (Classifier, RCA, Timeline, etc.)'],
    ['graph/', 'src/graph/', 'LangGraph state, nodes, builder, runner'],
    ['reporting/', 'src/reporting/', 'Markdown, JSON, CSV, previews, bundles'],
    ['evals/', 'src/evals/', 'GroundTruthLoader, scorer, metrics'],
    ['integrations/', 'src/integrations/', 'n8n webhooks (Slack, JIRA)']
]

mapping_table = Table(mapping_data, colWidths=[1.8*inch, 1.8*inch, 2.4*inch])
mapping_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a7a')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 8),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('FONTSIZE', (0, 1), (-1, -1), 7.5),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
]))
story.append(mapping_table)

story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("Additional Sections:", heading2_style))
additional = [
    "• <b>End-to-end runner</b> — Full pipeline orchestration",
    "• <b>Colab batch execution</b> — Run multiple datasets",
    "• <b>Smoke tests</b> — Validate on sample data",
    "• <b>Inspect results</b> — Debug incidents and scores",
    "• <b>Download bundle</b> — Export all outputs",
    "• <b>Refactor checklist</b> — Notes on moving code to src/"
]
for item in additional:
    story.append(Paragraph(item, normal_style))

story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("Why This Matters:", heading2_style))
v3_importance = """
v3 is intentionally modular — each cell's code is organized exactly as it should be in src/.
This makes it straightforward to refactor: copy working code from a notebook cell → move to
corresponding src/ file → test → integrate. The notebook serves as a bridge between
exploratory prototyping and production code.
"""
story.append(Paragraph(v3_importance, normal_style))
story.append(PageBreak())

# Section 5: Notebook v4
story.append(Paragraph("5. Multi_Agent_DevOps_Incident_Analysis_Suite_SRC_Aligned_Colab_v4.ipynb", heading1_style))
story.append(Paragraph("(111 KB) — Production-Ready Polished Implementation", heading2_style))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("<b>Purpose:</b> Latest, most complete reference implementation", normal_style))
story.append(Paragraph("<b>Status:</b> RECOMMENDED for use and as a reference", normal_style))
story.append(Paragraph("<b>What It Improves:</b> Bug fixes, enhanced diagnostics, better error handling", normal_style))
story.append(Spacer(1, 0.15*inch))

story.append(Paragraph("Improvements from v3 to v4:", heading2_style))
v4_improvements = [
    "• <b>v4 Stabilization Focus</b> — Production-grade refinements and bug fixes",
    "• <b>Better Diagnostics</b> — More detailed mismatch analysis in eval section",
    "• <b>LLM Connectivity Test</b> — Optional cell to validate OpenAI/OpenRouter setup",
    "• <b>Enhanced Inspection</b> — Eval mismatch diagnostics understand why incidents don't match",
    "• <b>Cleaner Code</b> — Refactored for clarity and maintainability",
    "• <b>Robust Error Handling</b> — Better exception handling in ingest and clustering",
    "• <b>Improved Evidence Citing</b> — RCA output includes better source references"
]
for improvement in v4_improvements:
    story.append(Paragraph(improvement, normal_style))

story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("New/Enhanced Features:", heading2_style))

v4_features_data = [
    ['Cell', 'Enhancement'],
    ['14b', 'Optional LLM connectivity smoke test'],
    ['16', 'Mismatch diagnostics: which incidents detected vs. ground truth?'],
    ['', 'Which categories were misclassified? Which severities wrong?'],
    ['', 'Which clusters should have been merged/split?']
]

v4_feat_table = Table(v4_features_data, colWidths=[1*inch, 5*inch])
v4_feat_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a7a')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('FONTSIZE', (0, 1), (-1, -1), 8),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
]))
story.append(v4_feat_table)

story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("Recommended Usage:", heading2_style))
usage = [
    "• <b>For learning:</b> Use v4 as the reference implementation",
    "• <b>For refactoring:</b> Copy code from v4 sections directly into src/ modules",
    "• <b>For testing:</b> Run v4 with sample datasets to validate behavior",
    "• <b>For extending:</b> Add new agents or reporters to v4 first, then migrate to src/"
]
for use in usage:
    story.append(Paragraph(use, normal_style))

story.append(PageBreak())

# Section 6: Feature Breakdown
story.append(Paragraph("6. Detailed Feature Breakdown", heading1_style))
story.append(Spacer(1, 0.15*inch))

story.append(Paragraph("Core Components (All 4 Notebooks Have These):", heading2_style))

features = [
    ("Input Validation & File Loading",
     ".zip extraction (safe), .jsonl/.log/.txt parsing, skip eval-only folders at runtime"),
    ("Log Normalization",
     "Parse raw lines into LogEvent objects with fields: timestamp, service, level, trace_id, message"),
    ("Signal Extraction",
     "Regex-based rules for database errors, network timeouts, auth failures; signal weights 0.0-1.0"),
    ("Clustering/Deduplication",
     "Group related signals into incident candidates; prevent duplicate reports"),
    ("Agent-Based Reasoning",
     "Classifier (category & severity), Timeline (chronology), RCA (root cause), Remediation, Critic"),
    ("Output Generation",
     "Outputs: Markdown reports, JSON/CSV exports, Slack/Teams previews, JIRA/GitHub previews, cookbooks"),
    ("n8n Integration",
     "Out-of-the-box support for n8n webhooks to dispatch Slack notifications and JIRA tickets"),
    ("Evaluation/Scoring",
     "Load ground truth, score category accuracy, severity accuracy, evidence grounding"),
]

for title, desc in features:
    story.append(Paragraph(f"<b>{title}</b>", heading2_style))
    story.append(Paragraph(desc, normal_style))
    story.append(Spacer(1, 0.1*inch))

story.append(PageBreak())

# Section 7: Data Flow
story.append(Paragraph("7. Data Flow Across Notebooks", heading1_style))
story.append(Spacer(1, 0.1*inch))

dataflow_text = """
<b>Step 1: Input</b><br/>
User uploads logs (ZIP or plaintext files)
<br/><br/>

<b>Step 2: Ingest</b><br/>
Parse & normalize into LogEvent objects
<br/><br/>

<b>Step 3: Signal Detection</b><br/>
Deterministic pattern matching extracts signals
<br/><br/>

<b>Step 4: Clustering</b><br/>
Group evidence into incident candidates
<br/><br/>

<b>Step 5: Agent Reasoning</b><br/>
LLM agents (with fallback to rules) perform:<br/>
&nbsp;&nbsp;&nbsp;&nbsp;• Classification (category, severity)<br/>
&nbsp;&nbsp;&nbsp;&nbsp;• Timeline building<br/>
&nbsp;&nbsp;&nbsp;&nbsp;• Root cause analysis<br/>
&nbsp;&nbsp;&nbsp;&nbsp;• Remediation recommendations<br/>
&nbsp;&nbsp;&nbsp;&nbsp;• Critic review (validate & reduce hallucinations)<br/>
<br/>

<b>Step 6: Reporting</b><br/>
Generate Markdown reports, JSON, CSV, preview notifications/tickets
<br/><br/>

<b>Step 7: Evaluation</b><br/>
Score against ground truth (eval-only step, isolated from runtime)
<br/><br/>

<b>Step 8: Download</b><br/>
User downloads bundle with all outputs
"""
story.append(Paragraph(dataflow_text, normal_style))
story.append(PageBreak())

# Section 8: How to Use
story.append(Paragraph("8. How to Use These Notebooks", heading1_style))
story.append(Spacer(1, 0.15*inch))

usage_table_data = [
    ['If You Want To...', 'Use This Notebook', 'Why'],
    ['Learn the core concepts', 'v1 (Original MVP)', 'Simplest agent structure, no graph complexity'],
    ['Understand LangGraph + LLM', 'v2 (LangGraph)', 'Introduces orchestration and state management'],
    ['Refactor code to src/', 'v3 (src/ Aligned)', 'Clear 1:1 mapping between cells and src/ files'],
    ['Run in practice', 'v4 (Production-Ready)', 'Latest, most stable, best diagnostics']
]

usage_tbl = Table(usage_table_data, colWidths=[1.5*inch, 1.5*inch, 2.5*inch])
usage_tbl.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a7a')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('FONTSIZE', (0, 1), (-1, -1), 8),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
]))
story.append(usage_tbl)

story.append(Spacer(1, 0.2*inch))
story.append(Paragraph("Workflow for Development:", heading2_style))
dev_workflow = [
    "1. <b>Understand:</b> Read the notebook cell-by-cell to understand the logic",
    "2. <b>Modify:</b> Change code and test in Colab to validate behavior",
    "3. <b>Extract:</b> Move working code from notebook cell to corresponding src/ file",
    "4. <b>Integrate:</b> Import from src/ back into notebook for validation",
    "5. <b>Test:</b> Run full pipeline to ensure integration works correctly"
]
for step in dev_workflow:
    story.append(Paragraph(step, normal_style))

story.append(PageBreak())

# Section 9: Key Takeaway
story.append(Paragraph("9. Key Takeaway", heading1_style))
story.append(Spacer(1, 0.15*inch))

takeaway = """
<b>v4 is the comprehensive reference implementation.</b><br/>
<br/>

Each section of v4 directly maps to a src/ module, making it straightforward to:<br/>
<br/>

1. <b>Understand</b> — Read the notebook cell-by-cell<br/>
2. <b>Modify</b> — Change logic and test in Colab<br/>
3. <b>Extract</b> — Move working code to src/ files<br/>
4. <b>Integrate</b> — Import from src/ back for validation<br/>
<br/>

The notebooks are intentionally modular. They serve as a bridge between:<br/>
• Exploratory prototyping (Google Colab environment)<br/>
• Production code (clean src/ modules)<br/>
<br/>

This design allows for rapid iteration and experimentation while ensuring that
eventually, the code is refactored into a maintainable, testable, production-grade codebase.
"""
story.append(Paragraph(takeaway, normal_style))

story.append(Spacer(1, 0.3*inch))
story.append(Paragraph("Happy Hacking! 🚀",
    ParagraphStyle('Footer', parent=styles['Normal'], fontSize=12,
                   alignment=TA_CENTER, fontName='Helvetica-Bold')))

# Build PDF
doc.build(story)
print(f"✓ PDF created: {output_path}")
print(f"  Location: {output_path}")
