# `src` Folder Guide — Multi-Agent DevOps Incident Analysis Suite

This `src/` folder is the implementation backbone for the final hackathon application. The Colab notebooks remain useful for experimentation, but the production-style implementation should live here as a clean, testable, modular Python codebase.

The project objective is to convert raw, mixed DevOps/SRE logs into evidence-backed incident analysis using deterministic Python components, LangGraph orchestration, LLM reasoning agents, optional RAG over runbooks, safe action previews, and evaluation against hidden ground truth.

## Target Outcome

The application should:

1. Ingest `.zip`, `.jsonl`, `.log`, and `.txt` operational logs.
2. Parse and normalize raw events without relying on visible labels.
3. Extract deterministic incident signals.
4. Cluster evidence into incident candidates.
5. Use LangGraph to coordinate specialized agents.
6. Infer incident category, severity, timeline, root cause, and remediation.
7. Generate Slack/Teams-style notification previews.
8. Generate JIRA/GitHub-style ticket previews.
9. Generate runbook/cookbook checklists.
10. Produce Markdown, JSON, CSV, and evaluation outputs.
11. Keep hidden ground truth isolated from runtime analysis.

---

## Current `src` Structure

```text
src/
  agents/
  clustering/
  config/
  evals/
  graph/
  ingest/
  models/
  rag/
  reporting/
  signals/
  utils/
  src_README.md
```

This README intentionally aligns with the actual folder structure above. Older references to `pipelines/` and `parsing/` have been removed. Their responsibilities are now split across `graph/`, `models/`, `ingest/`, and `signals/`.

---

## Architectural Principle

Use this split throughout the codebase:

```text
Python = deterministic evidence engine
LLM = reasoning and synthesis layer
LangGraph = orchestration and control flow
Pydantic models = shared contracts between components
RAG = operational knowledge retrieval
Adapters/previews = safe external action boundaries
```

Python should handle upload, extraction, parsing, normalization, signal matching, evidence references, clustering, exports, and deterministic scoring.

LLMs should handle ambiguous classification, root cause reasoning, symptom-vs-cause separation, severity rationale, remediation explanation, stakeholder messaging, missing-evidence analysis, and safe action planning.

LangGraph should handle state passing, node orchestration, conditional routing, retries, fallback paths, critique loops, and human approval gates.

---

## Folder Responsibilities and Recommended Classes

### `agents/`

Contains specialized reasoning and action-generation agents. Agents should be thin, focused classes that receive typed state/models and return structured outputs.

Recommended files/classes:

```text
base_agent.py              # BaseIncidentAgent, AgentResult
classifier_agent.py        # IncidentClassifierAgent
ambiguity_agent.py         # AmbiguityResolverAgent
symptom_cause_agent.py     # SymptomCauseAnalyzerAgent
timeline_agent.py          # TimelineAgent
rca_agent.py               # RootCauseAnalysisAgent
remediation_agent.py       # RemediationAgent
critic_agent.py            # SafetyCriticAgent, EvidenceGroundingCriticAgent
notification_agent.py      # NotificationPreviewAgent
ticket_agent.py            # TicketPreviewAgent
cookbook_agent.py          # CookbookSynthesisAgent
human_approval_agent.py    # HumanApprovalGateAgent
```

Purpose:
- Classify incident category and severity.
- Separate symptoms from likely root cause.
- Build timeline interpretation from evidence.
- Generate RCA with supporting and missing evidence.
- Recommend safe remediation and validation checks.
- Critique hallucination, unsupported claims, and unsafe actions.
- Generate preview-only notification and ticket payloads.
- Produce reusable incident cookbook/runbook checklists.
- Gate external actions behind human approval.

Implementation guidance:
- Agents should not read files directly.
- Agents should not access hidden ground truth.
- Agents should cite evidence using `source_file` and `line_no`.
- Agents should output Pydantic models from `models/`, not free-form dictionaries.

---

### `clustering/`

Contains evidence grouping logic that turns parsed events and extracted signals into incident candidates.

Recommended files/classes:

```text
evidence_clusterer.py       # EvidenceClusterer
cluster_strategy.py         # ClusterStrategy, HybridClusterStrategy
time_window_clusterer.py    # TimeWindowClusterer
service_clusterer.py        # ServiceClusterer
trace_clusterer.py          # TraceCorrelationClusterer
signature_clusterer.py      # ErrorSignatureClusterer
deduplicator.py             # IncidentDeduplicator
```

Purpose:
- Group noisy logs into actionable incident candidates.
- Cluster by time window, service, trace ID, signal type, error signature, and signal strength.
- Reduce duplicate symptom clusters.
- Prevent downstream agents from treating every error line as a separate incident.

MVP approach:

```text
file + candidate_category + affected_service
```

Final target:

```text
time window + service dependency + trace/correlation ID + repeated signature + signal weight
```

---

### `config/`

Contains runtime settings, constants, feature flags, and logging setup.

Recommended files/classes:

```text
settings.py          # AppSettings
llm_settings.py      # LLMSettings
rag_settings.py      # RAGSettings
eval_settings.py     # EvalSettings
logging_config.py    # configure_logging
constants.py         # IncidentCategory, SeverityLevel constants if not enum-based
```

Purpose:
- Load environment variables.
- Manage OpenAI/OpenRouter-compatible provider settings.
- Control feature flags such as LLM mode, preview mode, eval mode, and RAG mode.
- Store severity thresholds, evidence limits, and adapter settings.
- Avoid hardcoded values inside business logic.

Example settings:

```text
OPENAI_API_KEY
OPENAI_BASE_URL
MODEL_NAME
ENABLE_LLM_MODE
ENABLE_RAG_MODE
ENABLE_PREVIEW_MODE
ENABLE_EVAL_MODE
MAX_EVIDENCE_LINES
DEFAULT_TIME_WINDOW_MINUTES
MIN_SIGNAL_WEIGHT
```

---

### `evals/`

Contains evaluation and scoring logic. This is the only runtime area allowed to read hidden ground truth, and only after inference has completed.

Recommended files/classes:

```text
ground_truth_loader.py    # GroundTruthLoader
scorer.py                 # EvaluationScorer
metrics.py                # EvalMetrics
llm_judge.py              # LLMJudgeEvaluator
scorecard.py              # EvaluationScorecard
report.py                 # EvalReportBuilder
```

Purpose:
- Load `ground_truth_eval_only` files only during evaluation.
- Score category recall, severity accuracy, ticket-trigger accuracy, and evidence grounding.
- Optionally run LLM-as-judge for RCA quality, remediation usefulness, and safety.
- Produce evaluation summaries for the final hackathon report.

Important rule:

```text
Runtime graph nodes must never read ground_truth_eval_only.
Eval nodes may read ground truth only after inference output exists.
```

---

### `graph/`

Contains LangGraph state, nodes, routing, and graph construction. This replaces the older `pipelines/` responsibility.

Recommended files/classes:

```text
state.py                  # IncidentGraphState
nodes.py                  # Graph node functions
edges.py                  # routing and conditional edge helpers
builder.py                # IncidentGraphBuilder
runner.py                 # IncidentGraphRunner
fallbacks.py              # deterministic fallback routing
approval.py               # human approval gate routing
checkpointing.py          # checkpoint/session persistence hooks
```

Purpose:
- Define the shared LangGraph state contract.
- Connect ingestion, signal extraction, clustering, agents, reporting, and evals.
- Implement conditional routing for fallback mode, critic retry, and human approval.
- Keep orchestration separate from agent internals.

Recommended graph:

```text
START
  -> ingest_logs
  -> normalize_events
  -> extract_signals
  -> cluster_evidence
  -> classify_incident
  -> build_timeline
  -> analyze_symptom_vs_cause
  -> generate_rca
  -> retrieve_runbooks
  -> recommend_remediation
  -> critic_review
  -> human_approval_gate
  -> build_notification_preview
  -> build_ticket_preview
  -> synthesize_cookbook
  -> build_reports
  -> optionally_score_evals
END
```

For the MVP, the graph can run once per evidence cluster. For the final implementation, it should support multiple clusters and aggregate reporting.

---

### `ingest/`

Contains file loading, ZIP extraction, input validation, and raw event loading. It also owns lightweight parsing from files into raw event records.

Recommended files/classes:

```text
file_loader.py          # FileLoader
zip_loader.py           # SafeZipLoader
input_validator.py      # InputValidator
log_discovery.py        # LogFileDiscovery
raw_log_reader.py       # RawLogReader
log_parser.py           # LogParser
normalizer.py           # LogEventNormalizer
```

Purpose:
- Accept `.zip`, `.jsonl`, `.log`, and `.txt` files.
- Extract ZIP files safely and prevent path traversal.
- Identify runtime log files.
- Skip `ground_truth_eval_only` during runtime.
- Parse JSONL and plain text lines.
- Preserve malformed lines instead of silently dropping them.
- Normalize events into shared models from `models/`.

Expected normalized fields:

```text
source_file
line_no
timestamp
level
service
message
trace_id
span_id
host
namespace
pod
container
raw_line
parse_status
metadata
```

---

### `models/`

Contains typed data contracts shared across the whole application. This folder is essential because agents, graph nodes, reports, evals, and tests must exchange consistent objects.

Recommended files/classes:

```text
enums.py                # IncidentCategory, SeverityLevel, SignalType, ApprovalStatus
log_event.py            # LogEvent, RawLogLine, ParseResult
signal.py               # SignalMatch, SignalRule, SignalEvidence
cluster.py              # EvidenceCluster, ClusterSummary
incident.py             # IncidentCandidate, IncidentAnalysisResult
rca.py                  # RootCauseAnalysis, AlternativeCause, MissingEvidence
remediation.py          # RemediationPlan, RemediationAction, ValidationCheck, SafetyNote
timeline.py             # TimelineEvent, IncidentTimeline
runbook.py              # RunbookDocument, RunbookChunk, RunbookRetrievalResult
actions.py              # NotificationPayload, TicketPayload, CookbookChecklist
reports.py              # IncidentReport, ExportManifest
evals.py                # GroundTruthCase, EvalResult, EvalSummary
graph_state.py          # optional alias/import surface for IncidentGraphState
```

Purpose:
- Provide Pydantic models or dataclasses for all cross-module objects.
- Prevent unstructured dictionaries from spreading across the codebase.
- Make testing, validation, serialization, and reporting easier.
- Define stable contracts for LangGraph state and agent outputs.

Core enums should include:

```text
IncidentCategory:
  DATABASE
  NETWORK
  AUTHENTICATION
  MEMORY_CPU
  DEPLOYMENT_REGRESSION
  API_TIMEOUT
  QUEUE_BACKLOG
  DISK_STORAGE
  EXTERNAL_DEPENDENCY
  UNKNOWN

SeverityLevel:
  P1
  P2
  P3
  P4
  UNKNOWN

ApprovalStatus:
  PREVIEW_ONLY
  PENDING_HUMAN_APPROVAL
  APPROVED
  REJECTED
```

---

### `rag/`

Contains runbook/cookbook retrieval logic for RCA and remediation support.

Recommended files/classes:

```text
runbook_store.py       # RunbookStore
retriever.py           # RunbookRetriever
query_builder.py       # RetrievalQueryBuilder
embeddings.py          # EmbeddingProvider
vector_store.py        # VectorStore, FAISSVectorStore, ChromaVectorStore
chunker.py             # RunbookChunker
reranker.py            # RunbookReranker
```

Purpose:
- Store and retrieve operational knowledge.
- Provide relevant runbook guidance to RCA and remediation agents.
- Start with lexical/static retrieval for MVP.
- Upgrade to FAISS or Chroma for hackathon polish.
- Keep retrieval optional so fallback mode still works.

Recommended runbook chunk schema:

```text
service
incident_type
symptoms
diagnostics
remediation
validation
safety_notes
owner
source
```

---

### `reporting/`

Contains output generation and export logic.

Recommended files/classes:

```text
markdown_report.py        # MarkdownIncidentReportBuilder
json_exporter.py          # JsonExporter
csv_exporter.py           # CsvExporter
html_report.py            # HtmlReportBuilder
pdf_exporter.py           # PdfExporter, optional later
notification_preview.py   # NotificationPreviewBuilder
ticket_preview.py         # TicketPreviewBuilder
cookbook_exporter.py      # CookbookExporter
export_bundle.py          # OutputBundleBuilder
```

Purpose:
- Generate final incident reports.
- Export structured JSON and CSV outputs.
- Generate Slack/Teams-style notification previews.
- Generate JIRA/GitHub-style ticket previews.
- Generate cookbook/runbook checklists.
- Package outputs into a downloadable bundle.

For the hackathon, preview mode is preferred. Real Slack/JIRA writes should be adapter-based and human-approved.

---

### `signals/`

Contains deterministic signal extraction rules and severity heuristics.

Recommended files/classes:

```text
rules.py                  # built-in SignalRule definitions
rule_engine.py            # SignalRuleEngine
signal_extractor.py       # SignalExtractor
severity_rules.py         # SeverityHeuristicEngine
category_rules.py         # CategoryHeuristicEngine
pattern_library.py        # RegexPatternLibrary
signal_weights.py         # SignalWeightRegistry
```

Purpose:
- Detect operational signals using regex/rules.
- Identify database, network, authentication, memory/CPU, deployment, API timeout, queue, disk, external dependency, and unknown signals.
- Assign signal weights and severity hints.
- Provide evidence lines for downstream agents.

This layer should be deterministic and evidence-backed. It should generate candidates, not pretend to know final root cause.

---

### `utils/`

Contains shared helper functions with no business ownership.

Recommended files/classes:

```text
file_utils.py       # safe paths, file naming, directory cleanup
time_utils.py       # timestamp parsing, time windows
json_utils.py       # safe JSON read/write
text_utils.py       # truncation, redaction, normalization
hash_utils.py       # stable IDs and content hashes
logging_utils.py    # shared logging helpers
errors.py           # custom exceptions
```

Purpose:
- Keep reusable helpers out of domain modules.
- Avoid placing agent, graph, or signal business logic here.
- Provide safe file, time, JSON, text, and logging utilities.

---

## Runtime Data Boundary

Runtime analysis must only read raw operational logs:

```text
raw_logs/
```

Runtime analysis must not read:

```text
ground_truth_eval_only/
```

Hidden labels such as expected category, expected severity, scenario ID, or remediation labels are eval-only. This protects the demo from becoming a label lookup exercise.

---

## Recommended Minimum Implementation Order

Start with this order to create a stable final implementation:

```text
src/models/enums.py
src/models/log_event.py
src/models/signal.py
src/models/cluster.py
src/models/incident.py
src/config/settings.py
src/ingest/input_validator.py
src/ingest/zip_loader.py
src/ingest/log_discovery.py
src/ingest/log_parser.py
src/ingest/normalizer.py
src/signals/rules.py
src/signals/rule_engine.py
src/signals/signal_extractor.py
src/clustering/evidence_clusterer.py
src/agents/classifier_agent.py
src/agents/timeline_agent.py
src/agents/rca_agent.py
src/agents/remediation_agent.py
src/agents/critic_agent.py
src/graph/state.py
src/graph/builder.py
src/graph/runner.py
src/reporting/markdown_report.py
src/reporting/json_exporter.py
src/evals/scorer.py
```

Then add:

```text
src/rag/retriever.py
src/rag/vector_store.py
src/agents/notification_agent.py
src/agents/ticket_agent.py
src/agents/cookbook_agent.py
src/agents/human_approval_agent.py
src/reporting/export_bundle.py
src/evals/llm_judge.py
```

---

## What Was Removed From the Older README

The older README referred to folders that are not present in the current `src/` structure:

```text
parsing/
pipelines/
```

These were removed from the documented structure.

Responsibility mapping:

```text
old parsing/   -> ingest/log_parser.py + ingest/normalizer.py + models/log_event.py
old pipelines/ -> graph/state.py + graph/builder.py + graph/runner.py
```

This keeps the README consistent with the actual folders shown under `src/`.

---

## What Not to Add Yet

Avoid adding these until the core incident analysis flow is stable:

```text
frontend/
api/
db/
adapters/slack/
adapters/jira/
deployment/
docker/
kubernetes/
```

Reason:
The immediate priority is to convert notebook logic into clean Python modules. UI, API, real Slack/JIRA integration, and deployment can come after the core graph, models, evidence engine, and reports are working.

---

## What to Avoid

Avoid duplicate folders or overlapping names:

```text
parser/
parsers/
log_reader/
workflow/
orchestration/
pipeline/
pipelines/
```

Use the current names consistently:

```text
ingest/   # file loading, raw reading, parsing, normalization
graph/    # LangGraph state, nodes, edges, runner
models/   # typed contracts and schemas
```

Also avoid committing:

```text
__pycache__/
.ipynb_checkpoints/
.env
*.log
*.tmp
large generated outputs
local test downloads
```

---

## Definition of Done for Final Hackathon Implementation

The `src/` implementation is ready when it can:

1. Load raw mixed logs from a ZIP.
2. Skip hidden eval folders during runtime.
3. Normalize logs into typed `LogEvent` objects.
4. Extract deterministic `SignalMatch` evidence.
5. Build `EvidenceCluster` objects.
6. Run the LangGraph workflow over clusters.
7. Produce category, severity, RCA, remediation, timeline, notification preview, ticket preview, and cookbook output.
8. Cite evidence by file and line number.
9. Require human approval before any external action.
10. Run eval scoring only after inference.
11. Export Markdown, JSON, and CSV outputs.
12. Run in fallback deterministic mode if no LLM key is configured.

---

## Final Implementation Story

```text
Upload raw mixed production logs.
Python extracts grounded evidence.
LangGraph coordinates specialist agents.
LLMs reason over ambiguity and missing context.
RAG retrieves operational runbooks.
Critic agents check safety and evidence grounding.
Humans approve external actions.
Reports and evals prove the result.
```

This is the intended base architecture for the final hackathon build.
