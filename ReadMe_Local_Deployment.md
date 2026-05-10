# IncidentIQ Local Deployment Guide

This guide explains how to run and test IncidentIQ locally with the Gradio UI.

## 1. Prerequisites

- Python 3.9+
- `pip`
- Repository checked out locally
- Terminal opened at the repository root

Repository root example:

```bash
cd /Users/vikrantgupta/Documents/IncidentIQ
```

## 2. Create Or Verify `.env`

The app reads configuration from the root `.env` file.

Important values:

```env
INCIDENTIQ_WORK_ROOT=/tmp/incidentiq_work
ENABLE_RAG_MODE=true
ENABLE_EVAL_MODE=true
ENABLE_PREVIEW_MODE=true
ENABLE_REAL_INTEGRATIONS=false
workDir=/Users/vikrantgupta/Documents/IncidentIQ/src/rag
INCIDENTIQ_RAG_TOP_K=5
PORT=8765
GRADIO_SERVER_NAME=127.0.0.1
JIRA_BASE_URL=https://jira.example.com
JIRA_PROJECT_KEY=OPS
SLACK_CHANNEL=#devops-incidents
```

Secrets and future integration keys also live in `.env`:

```env
JIRA_EMAIL=
JIRA_API_TOKEN=
SLACK_WEBHOOK_URL=
OPENROUTER_API_KEY=
OPENAI_API_KEY=
```

Keep `.env` out of git. It is already listed in `.gitignore`.

## 3. Install Dependencies

Recommended:

```bash
python3 -m pip install -r requirements.txt
```

If you only want the deterministic local demo path, the critical packages are:

```bash
python3 -m pip install gradio pandas pydantic python-dateutil python-dotenv
```

The app works with local lexical RAG by default. FAISS/vector search dependencies are optional for local testing.

## 4. Run The Local Gradio App

Start the app:

```bash
python3 -B app.py
```

Open:

```text
http://127.0.0.1:8765
```

The UI provides:

- Upload report/log file
- Backend progress checklist
- Final incident result
- Dummy Jira links
- Downloadable ZIP, JSON, Markdown, and CSV outputs

## 5. Test With Bundled Sample Data

Use this sample ZIP in the UI:

```text
datasets/incidentiq_small_test_sample_easy.zip
```

Or run the command-line smoke test:

```bash
python3 -B scripts/smoke_test.py
```

Expected smoke-test result:

- Status: `completed`
- Events parsed: greater than `0`
- Signals found: greater than `0`
- Incidents found: greater than `0`
- Highest severity: usually `P1`
- Output ZIP generated under `/tmp/incidentiq_work/runs/...`

## 6. RAG Behavior

RAG is connected through:

```text
app.py
  -> src.pipeline.analyze_uploaded_logs
  -> src.pipeline.retrieve_runbook_context
  -> src.rag.retrieve_rag_context
```

Current default RAG mode:

- Uses local text files from `src/rag/knowledge_base`
- Does not require API keys
- Does not require FAISS
- Retrieves SOPs, error mappings, and architecture notes lexically

Current knowledge base includes:

- Database connection pool SOP
- Authentication JWT failure SOP
- API timeout cascade SOP
- Memory/CPU saturation SOP
- Kafka queue backlog SOP
- Disk/storage pressure SOP
- Deployment regression SOP
- Network/external/unknown triage SOP
- Known error mappings
- Production architecture overview

Optional FAISS index path:

```text
src/rag/faiss_index
```

If this folder does not exist, the app still works with local lexical RAG.

## 7. Generated Outputs

Each run writes files under:

```text
/tmp/incidentiq_work/runs/<run_id>/
```

Outputs include:

```text
outputs/analysis_response.json
outputs/incident_report.md
outputs/incidents.csv
outputs/evidence_clusters.csv
<run_id>_outputs.zip
```

## 8. Local Troubleshooting

### Port Already In Use

Check the configured port:

```bash
cat .env | grep PORT
```

Change `PORT=8765` to another port, for example:

```env
PORT=8770
```

Then restart:

```bash
python3 -B app.py
```

### Permission Error When Starting Server

Some sandboxed environments block local socket binding. Run the app from a normal local terminal, or allow the command when prompted by the development environment.

### `.env` Changes Not Reflected

Restart the app after editing `.env`.

### No Incidents Found

Check that uploaded files are one of:

```text
.zip, .jsonl, .log, .txt, .json
```

For ZIP uploads, runtime logs should be under a path containing:

```text
raw_logs
```

Ground-truth files under `ground_truth_eval_only` are intentionally skipped during inference and used only for optional scoring.

### RAG Sources Missing

Verify:

```bash
ls src/rag/knowledge_base
```

Also confirm:

```bash
python3 -B -c "from src.rag.rag_retriever import _read_docs; print(len(_read_docs()))"
```

Expected result: at least `1`; current project has `10`.

## 9. Safety Defaults

Local deployment is safe by default:

- Jira links are dummy preview links.
- Slack payloads are preview-only.
- Real integrations are disabled with `ENABLE_REAL_INTEGRATIONS=false`.
- Human approval is required before disruptive remediation.
- Hidden labels are not used during runtime inference.

## 10. Quick Command Summary

```bash
cd /Users/vikrantgupta/Documents/IncidentIQ
python3 -m pip install -r requirements.txt
python3 -B scripts/smoke_test.py
python3 -B app.py
```

Then open:

```text
http://127.0.0.1:8765
```
