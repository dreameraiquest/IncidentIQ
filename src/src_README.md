# `src` Folder Guide — IncidentIQ / Multi-Agent DevOps Incident Analysis Suite

This folder contains the Python source-code modules for the real application version of the project. The earlier Colab notebooks are only experimentation and team-sharing artifacts. The final implementation should use this `src` structure as the maintainable codebase.

## Recommended `src` Structure

```text
src/
  agents/
  clustering/
  config/
  evals/
  ingest/
  parsing/
  pipelines/
  rag/
  reporting/
  signals/
  utils/
```

## Folder Responsibilities

### `agents/`
Contains agent-level logic used by the LangGraph workflow.

Suggested future files:

```text
classifier_agent.py
rca_agent.py
remediation_agent.py
critic_agent.py
notification_agent.py
ticket_agent.py
cookbook_agent.py
```

Purpose:
- Classify incident category and severity.
- Generate root cause analysis.
- Recommend safe remediation steps.
- Review outputs for hallucination/safety risk.
- Generate Slack/Teams-style notification previews.
- Generate JIRA/GitHub-style ticket previews.
- Generate cookbook/runbook checklists.

For now, keep this folder empty except for `__init__.py` if needed.

---

### `clustering/`
Contains evidence grouping logic.

Suggested future files:

```text
evidence_clusterer.py
time_window_clusterer.py
service_clusterer.py
```

Purpose:
- Group parsed log events into incident candidates.
- Cluster by category, service, timestamp, trace ID, and signal strength.
- Reduce noisy logs into actionable evidence groups.

For the first version, clustering can be simple: `file + candidate_category`. Later, improve it using time windows, service dependency, trace correlation, and repeated error signatures.

---

### `config/`
Contains configuration and environment handling.

Suggested future files:

```text
settings.py
logging_config.py
constants.py
```

Purpose:
- Load environment variables.
- Manage LLM provider settings.
- Store default thresholds, severity rules, adapter flags, and runtime options.
- Keep hardcoded values out of business logic.

Example settings:
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `MODEL_NAME`
- `ENABLE_LLM_MODE`
- `ENABLE_PREVIEW_MODE`
- `MAX_EVIDENCE_LINES`

---

### `evals/`
Contains scoring and validation logic.

Suggested future files:

```text
scorer.py
metrics.py
ground_truth_loader.py
```

Purpose:
- Load hidden ground truth only during evaluation.
- Score category detection.
- Score severity accuracy.
- Score ticket trigger accuracy.
- Produce evaluation summary reports.

Important rule:
Runtime analysis must not read `ground_truth_eval_only`. Ground truth should be used only after inference is complete.

---

### `ingest/`
Contains file loading and upload handling.

Suggested future files:

```text
file_loader.py
zip_loader.py
input_validator.py
```

Purpose:
- Accept `.zip`, `.jsonl`, `.log`, and `.txt` files.
- Extract ZIP files safely.
- Identify raw log files.
- Skip hidden eval folders during runtime.
- Preserve source file paths for evidence references.

---

### `parsing/`
Contains deterministic log parsing and normalization.

Suggested future files:

```text
log_parser.py
normalizer.py
schema.py
```

Purpose:
- Parse JSONL and plain text logs.
- Extract timestamp, level, service, message, trace ID, and metadata.
- Preserve malformed lines instead of silently dropping them.
- Convert raw logs into a common event schema.

Expected normalized event fields:

```text
source_file
line_no
timestamp
level
service
message
trace_id
raw_line
```

---

### `pipelines/`
Contains orchestration-level workflow code.

Suggested future files:

```text
langgraph_workflow.py
pipeline_runner.py
state.py
```

Purpose:
- Define the LangGraph state.
- Connect parser, signal extractor, clusterer, agents, reporting, and evals.
- Control the full incident analysis flow.
- Support fallback deterministic mode when no LLM key is available.

Expected flow:

```text
ingest_logs
parse_logs
extract_signals
cluster_evidence
classifier_agent
timeline_agent
rca_agent
remediation_agent
critic_agent
action_builder
report_builder
```

---

### `rag/`
Contains runbook retrieval logic.

Suggested future files:

```text
runbook_store.py
retriever.py
embeddings.py
```

Purpose:
- Store and retrieve runbook/cookbook knowledge.
- Support remediation and RCA agents with relevant operational guidance.
- Start with static/lexical retrieval.
- Later upgrade to FAISS, Chroma, Azure AI Search, Pinecone, OpenSearch, or another vector database.

For now, this folder can remain lightweight.

---

### `reporting/`
Contains output generation.

Suggested future files:

```text
markdown_report.py
json_exporter.py
csv_exporter.py
notification_preview.py
ticket_preview.py
cookbook_exporter.py
```

Purpose:
- Generate final incident reports.
- Export JSON and CSV outputs.
- Generate Slack/Teams-style notification previews.
- Generate JIRA/GitHub-style ticket previews.
- Generate cookbook/runbook checklists.

For the hackathon, preview mode is acceptable. Real Slack/JIRA integration can be added later through adapters.

---

### `signals/`
Contains deterministic signal extraction rules.

Suggested future files:

```text
rules.py
signal_extractor.py
severity_rules.py
```

Purpose:
- Detect operational signals using regex/rules.
- Identify database, network, authentication, memory/CPU, deployment, API timeout, queue, disk, external dependency, and unknown signals.
- Assign signal weights.
- Provide evidence lines for downstream agents.

This layer should be deterministic and evidence-backed.

---

### `utils/`
Contains shared helper functions.

Suggested future files:

```text
file_utils.py
time_utils.py
json_utils.py
text_utils.py
logging_utils.py
```

Purpose:
- Reusable utilities that do not belong to a specific domain module.
- Keep business logic out of utility files.
- Avoid putting agent-specific or pipeline-specific logic here.

---

## What to Keep for Now

Keep these folders:

```text
agents/
clustering/
config/
evals/
ingest/
parsing/
pipelines/
rag/
reporting/
signals/
utils/
```

This structure is good for the current project and maps cleanly to the hackathon problem statement.

## What Not to Add Yet

Do not add these until the prototype stabilizes:

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
The immediate priority is to convert notebook logic into clean Python modules. UI, APIs, real Slack/JIRA integrations, and deployment can come after the core pipeline is stable.

## What to Remove or Avoid

Avoid duplicate folders with overlapping responsibilities, such as:

```text
parser/
parsers/
log_reader/
workflow/
graph/
orchestration/
```

Use the current names consistently:

```text
parsing/      # parsing logic
pipelines/    # orchestration / LangGraph workflow
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

## Recommended Minimum Files Later

When ready to add Python files, start with these:

```text
src/config/settings.py
src/ingest/file_loader.py
src/parsing/log_parser.py
src/signals/rules.py
src/signals/signal_extractor.py
src/clustering/evidence_clusterer.py
src/pipelines/state.py
src/pipelines/langgraph_workflow.py
src/reporting/markdown_report.py
src/evals/scorer.py
```

Then add agents one by one:

```text
src/agents/classifier_agent.py
src/agents/rca_agent.py
src/agents/remediation_agent.py
src/agents/critic_agent.py
src/agents/notification_agent.py
src/agents/ticket_agent.py
src/agents/cookbook_agent.py
```

## Design Principle

Use this split:

```text
Python = deterministic evidence engine
LLM = reasoning and synthesis layer
LangGraph = orchestration and control flow
```

Python should handle upload, parsing, normalization, regex signal extraction, clustering, evidence references, report exports, and eval scoring.

LLMs should handle ambiguous classification, RCA reasoning, severity rationale, remediation explanation, stakeholder communication, missing evidence analysis, and safe action planning.

LangGraph should handle state passing, node orchestration, retries, fallback paths, critique loops, and human approval gates.

## Current Status

The current `src` structure is acceptable. No internal `.py` files are required yet. This README can be committed under `src/` to document the intended architecture before implementation begins.
