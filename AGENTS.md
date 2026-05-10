# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

**IncidentIQ** is a multi-agent AI platform for DevOps incident detection, root cause analysis (RCA), and automated response. It ingests raw production logs and orchestrates specialized LangGraph agents to:

- Detect incident signals from noisy, unlabeled logs
- Classify incidents by category (Database, Network, Authentication, etc.) and severity (P1/P2/P3)
- Reconstruct incident timelines from evidence
- Perform evidence-backed RCA
- Recommend safe remediation actions
- Generate Slack/Teams notification previews and JIRA/GitHub ticket previews
- Create reusable runbooks and cookbooks
- Evaluate results against hidden ground truth

**Technology Stack:**
- Python 3.11+ with Pydantic for type safety
- LangGraph for multi-agent orchestration
- LangChain for LLM abstraction
- OpenAI/OpenRouter-compatible LLM APIs
- FAISS/Chroma for vector search over runbooks
- Streamlit/Jupyter for notebook experimentation

## Repository Structure

```
IncidentIQ/
├── src/              # Production-oriented modular implementation
├── datasets/         # Raw and eval-only test data
├── docs/             # Architecture diagrams and design notes
│   └── notebooks/    # Colab/Jupyter experimentation and prototypes
├── requirements.txt  # Python dependencies
├── README.md         # Full project documentation
└── AGENTS.md         # This file
```

**Important:** Maintainable production code lives in `src/`. Notebooks are for experimentation only.

## Common Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run a specific notebook (experimental/prototype work)
jupyter notebook docs/notebooks/Multi_Agent_DevOps_Incident_Analysis_Suite_SRC_Aligned_Colab_v4.ipynb

# If implementing src/ modules, test individual components with Python
python -c "from src.models.enums import IncidentCategory; print(IncidentCategory.DATABASE)"

# (Future) Run tests
pytest tests/  # Not yet set up; create as implementation grows

# (Future) Run linting/formatting
black src/
flake8 src/
```

## Architecture at a Glance

The project follows a clean separation of concerns:

```
Raw Logs
   ↓
[Ingest: Parse & Normalize]
   ↓
[Signals: Extract Rules-Based Evidence]
   ↓
[Clustering: Group Related Evidence]
   ↓
[LangGraph Orchestration] ←── Deterministic Python Layer
   ├── LLM Agents (Classify, Timeline, RCA, Remediation, Critic)
   └── RAG (Optional Runbook Retrieval)
   ↓
[Reporting: Generate Outputs]
   ↓
[Evals: Score Against Ground Truth]
```

### Key Architectural Principles

1. **Python = Deterministic Evidence**: File loading, parsing, normalization, signal extraction, clustering, and deterministic scoring all use pure Python. No hallucination risk.

2. **LLMs = Reasoning Layer**: Ambiguous classification, RCA rationale, symptom-vs-cause separation, severity justification, remediation explanation, and safe action planning use LLMs.

3. **LangGraph = Orchestration**: State passing, agent routing, conditional edges, retry loops, critic feedback, and human approval gates happen in the LangGraph graph definition.

4. **Evidence Grounding**: All conclusions must cite source file and line number. RAG, RCA, and remediation outputs include supporting and missing evidence references.

5. **Safe Boundaries**: Notification and ticket generation are preview-only by default. Real Slack/JIRA writes require human approval.

6. **Eval Isolation**: Runtime analysis never reads `ground_truth_eval_only/` data. Evaluation happens only after inference completes, protecting the demo from label lookup.

## src/ Folder Responsibilities

### `src/models/`
**Typed data contracts** using Pydantic. All cross-module communication uses these shared objects.

Key files:
- `enums.py` — IncidentCategory, SeverityLevel, SignalType, ApprovalStatus
- `log_event.py` — LogEvent, RawLogLine, ParseResult
- `signal.py` — SignalMatch, SignalRule, SignalEvidence
- `cluster.py` — EvidenceCluster, ClusterSummary
- `incident.py` — IncidentCandidate, IncidentAnalysisResult
- `rca.py` — RootCauseAnalysis, AlternativeCause, MissingEvidence
- `remediation.py` — RemediationPlan, RemediationAction, ValidationCheck, SafetyNote
- `timeline.py` — TimelineEvent, IncidentTimeline
- `actions.py` — NotificationPayload, TicketPayload, CookbookChecklist
- `reports.py` — IncidentReport, ExportManifest

### `src/ingest/`
**File loading, parsing, normalization**. Handles `.zip`, `.jsonl`, `.log`, and `.txt` files.

Key files:
- `file_loader.py` — FileLoader class
- `zip_loader.py` — SafeZipLoader (prevents path traversal)
- `log_parser.py` — LogParser (JSONL and plaintext)
- `normalizer.py` — LogEventNormalizer (converts raw lines to LogEvent objects)

Responsibility: Preserve malformed lines, skip eval-only folders, maintain source/line references.

### `src/signals/`
**Deterministic signal extraction** using regex rules and pattern matching.

Key files:
- `rules.py` — Built-in SignalRule definitions (database, network, auth, memory, etc.)
- `rule_engine.py` — SignalRuleEngine (applies rules to log events)
- `signal_extractor.py` — SignalExtractor (main interface)
- `severity_rules.py` — SeverityHeuristicEngine (weights for P1/P2/P3 hints)

Responsibility: Extract evidence-backed signals; assign weights; suggest severity hints but don't claim final severity.

### `src/clustering/`
**Evidence grouping** into actionable incident candidates.

Key files:
- `evidence_clusterer.py` — EvidenceClusterer (main class)
- `cluster_strategy.py` — ClusterStrategy, HybridClusterStrategy

MVP approach: Group by `(file, category, service)`. Target: time window + service dependency + trace ID + signal weight.

### `src/agents/`
**Specialized reasoning and action agents**. Thin, focused classes that ingest typed state and return Pydantic models.

Agents should:
- Never read files directly
- Never access hidden ground truth
- Cite evidence by file and line number
- Return structured Pydantic models, not dicts
- Accept evidence clusters as input; reason over ambiguity

Key agents:
- `classifier_agent.py` — IncidentClassifierAgent (infer category & severity)
- `timeline_agent.py` — TimelineAgent (build incident chronology)
- `rca_agent.py` — RootCauseAnalysisAgent (perform evidence-backed RCA)
- `remediation_agent.py` — RemediationAgent (suggest safe recovery actions)
- `critic_agent.py` — SafetyCriticAgent, EvidenceGroundingCriticAgent (validate reasoning)
- `notification_agent.py` — NotificationPreviewAgent (Slack/Teams preview)
- `ticket_agent.py` — TicketPreviewAgent (JIRA/GitHub preview)
- `cookbook_agent.py` — CookbookSynthesisAgent (runbook/checklist generation)

### `src/rag/`
**Runbook/cookbook retrieval for RCA and remediation support**.

Key files:
- `runbook_store.py` — RunbookStore (loads and indexes runbooks)
- `retriever.py` — RunbookRetriever (lexical and semantic search)
- `vector_store.py` — FAISSVectorStore, ChromaVectorStore (optional)

MVP approach: Lexical/keyword retrieval. Upgrade to FAISS for hackathon polish. Fallback mode works without RAG.

### `src/graph/`
**LangGraph state, nodes, and orchestration**. Replaces older `pipelines/` responsibility.

Key files:
- `state.py` — IncidentGraphState (shared state contract)
- `nodes.py` — Graph node functions
- `edges.py` — Routing and conditional edge helpers
- `builder.py` — IncidentGraphBuilder (constructs the graph)
- `runner.py` — IncidentGraphRunner (executes and checkpoints)

Recommended graph flow:
```
ingest_logs
  → normalize_events
  → extract_signals
  → cluster_evidence
  → classify_incident
  → build_timeline
  → analyze_symptom_vs_cause
  → generate_rca
  → retrieve_runbooks
  → recommend_remediation
  → critic_review
  → human_approval_gate
  → build_notification_preview
  → build_ticket_preview
  → synthesize_cookbook
  → build_reports
  → optionally_score_evals
```

### `src/reporting/`
**Output generation and export**.

Key files:
- `markdown_report.py` — MarkdownIncidentReportBuilder
- `json_exporter.py` — JsonExporter
- `csv_exporter.py` — CsvExporter
- `notification_preview.py` — NotificationPreviewBuilder (Slack/Teams style)
- `ticket_preview.py` — TicketPreviewBuilder (JIRA/GitHub style)
- `cookbook_exporter.py` — CookbookExporter
- `export_bundle.py` — OutputBundleBuilder

### `src/evals/`
**Evaluation and scoring against hidden ground truth**. ONLY this module reads `ground_truth_eval_only/` data, and only after inference completes.

Key files:
- `ground_truth_loader.py` — GroundTruthLoader
- `scorer.py` — EvaluationScorer
- `metrics.py` — EvalMetrics (recall, precision, accuracy)
- `llm_judge.py` — LLMJudgeEvaluator (optional RCA quality scoring)

### `src/config/`
**Settings and feature flags**. All hardcoded values go here.

Key files:
- `settings.py` — AppSettings (environment variables, API keys, model names)
- `logging_config.py` — configure_logging()

Example env vars:
```
OPENAI_API_KEY
OPENAI_BASE_URL
MODEL_NAME
ENABLE_LLM_MODE
ENABLE_RAG_MODE
ENABLE_PREVIEW_MODE
ENABLE_EVAL_MODE
MAX_EVIDENCE_LINES
DEFAULT_TIME_WINDOW_MINUTES
```

### `src/utils/`
**Reusable helpers** with no domain ownership.

Key files:
- `file_utils.py` — Safe file operations, path validation
- `time_utils.py` — Timestamp parsing, time windows
- `json_utils.py` — Safe JSON read/write
- `text_utils.py` — Truncation, redaction, normalization
- `hash_utils.py` — Stable content hashes for IDs
- `errors.py` — Custom exceptions

## Data Boundaries

### Runtime Analysis (Always Allowed)
```
datasets/block1_quick_raw/
datasets/block2_full_raw/
(or any raw_logs/ data)
```

### Eval-Only Data (Never Touched at Runtime)
```
ground_truth_eval_only/  # ← Only read after inference finishes
```

**Rule:** Runtime graph nodes must never read ground truth files. Evals may read ground truth only after inference output exists and is written to disk.

## Implementation Order (for adding new modules)

Start with this order to build a stable foundation:

1. **Models** (`src/models/`) — Type contracts first
2. **Ingest** (`src/ingest/`) — File loading and normalization
3. **Signals** (`src/signals/`) — Rule-based signal extraction
4. **Clustering** (`src/clustering/`) — Evidence grouping
5. **Agents** (`src/agents/`) — Classifier, Timeline, RCA, Remediation, Critic
6. **Graph** (`src/graph/`) — Orchestration and state management
7. **Reporting** (`src/reporting/`) — Output generation
8. **Evals** (`src/evals/`) — Evaluation and scoring
9. **RAG** (`src/rag/`) — Runbook retrieval (optional, can be added later)

## Key Development Notes

### Pydantic Models
- All cross-module objects should be Pydantic models (from `src/models/`)
- Avoid passing raw dictionaries across boundaries
- Models auto-validate at construction time

### Enum Usage
- Use `src/models/enums.py` for IncidentCategory, SeverityLevel, SignalType, ApprovalStatus
- These enums are shared across agents, clustering, and reporting

### Evidence Grounding
- Every SignalMatch and claimed root cause must reference `source_file` and `line_no`
- Agents should explain what evidence supports their reasoning
- Fallback: if evidence is missing, agents should state "missing evidence for X"

### LLM Prompts
- Store prompt templates in agent modules or a separate `src/prompts/` folder (if adding one)
- Use Pydantic models in LLM input/output schemas for validation
- Consider prompt caching (OpenAI `cache_control`) for repeated queries

### Testing
- As modules grow, create `tests/` directory with pytest
- Test ingest, signal extraction, and clustering deterministically
- Mock LLM calls in agent tests or use replay fixtures
- Evals serve as integration tests by comparing outputs to ground truth

### Environment Setup
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### Common Pitfalls
- **Don't hardcode settings** — Use `src/config/settings.py`
- **Don't skip evidence references** — Always cite file + line number
- **Don't read eval files at runtime** — Isolate to evals module only
- **Don't mix agent business logic with graph orchestration** — Keep agents stateless
- **Don't assume log structure** — Handle malformed lines gracefully

## Incident Categories

IncidentIQ supports detection of:
- Database Failures
- Network Outages
- Authentication Issues
- Memory / CPU Pressure
- Deployment Regressions
- API Timeouts
- Queue Backlogs
- Disk / Storage Failures
- External Dependency Failures
- Unknown / Ambiguous Incidents

## Severity Levels

- **P1** — Critical, affects users, requires immediate action
- **P2** — Major, degrades functionality, action needed soon
- **P3** — Minor, informational, can be scheduled
- **Unknown** — Insufficient evidence for severity classification

## Important Files to Review

- [README.md](README.md) — Full project vision and feature list
- [src/src_README.md](src/src_README.md) — Detailed src/ architecture guide
- [docs/notebooks/Multi_Agent_DevOps_Incident_Analysis_Suite_SRC_Aligned_Colab_v4.ipynb](docs/notebooks/Multi_Agent_DevOps_Incident_Analysis_Suite_SRC_Aligned_Colab_v4.ipynb) — Latest prototype and workflow validation
- [Hackthon Project Description.txt](Hackthon%20Project%20Description.txt) — Use case summary

## Future Enhancements

The MVP is Python + LangGraph + in-memory models. The planned production stack includes:
- FastAPI backend
- React frontend
- PostgreSQL for persistence
- Real Slack/JIRA integrations (behind human approval gates)
- OpenTelemetry trace correlation
- Kubernetes & cloud-native integrations
