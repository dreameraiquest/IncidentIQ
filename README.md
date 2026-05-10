# IncidentIQ 🚨
## Multi-Agent AI Platform for DevOps Incident Detection, RCA & Automated Response

IncidentIQ is an AI-powered multi-agent DevOps incident analysis platform that transforms raw production logs into evidence-backed incident intelligence, root cause analysis (RCA), remediation guidance, and operational action plans.

Built using LangGraph, LLMs, and deterministic evidence extraction pipelines, IncidentIQ acts like an AI Incident Commander for SRE and DevOps teams. The system ingests noisy, mixed, production-style logs and orchestrates specialized agents to detect incidents, infer severity, reconstruct timelines, identify probable root causes, recommend safe remediation actions, and generate collaboration-ready outputs such as Slack alerts and GitHub/JIRA ticket previews.


---

<p align="center">
  <img src="docs/diagrams/IncidentIQ Flowchart - The Multi-Agent Evolution of DevOps Incident Analysis.png" alt="IncidentIQ multi-agent DevOps incident analysis workflow" width="900">
</p>

---

## ✨ Key Features

- Upload raw `.jsonl`, `.log`, `.txt`, or `.zip` production logs
- Multi-agent LangGraph orchestration pipeline
- Intelligent incident signal extraction from noisy logs
- Evidence clustering & timeline reconstruction
- AI-driven Root Cause Analysis (RCA)
- Automated severity classification (P1/P2/P3)
- Safe remediation recommendations
- Slack/Teams-style notification previews
- GitHub/JIRA-style ticket previews
- Cookbook & runbook generation
- Evaluation scoring against hidden ground truth
- Human-in-the-loop approval workflow

---

## 🏗 Architecture Overview

```text
Raw Logs
   ↓
Parser & Normalization Engine
   ↓
Signal Extraction
   ↓
Evidence Clustering
   ↓
LangGraph Multi-Agent Workflow
   ├── Classifier Agent
   ├── Timeline Agent
   ├── RCA Agent
   ├── Remediation Agent
   ├── Critic Agent
   └── Action Builder
   ↓
Incident Reports + Notifications + Tickets + Runbooks
```

---

## 🤖 Multi-Agent Workflow

| Agent | Responsibility |
|---|---|
| Parser Agent | Normalize logs into structured events |
| Signal Extraction Agent | Detect operational incident signals |
| Evidence Clustering Agent | Group related evidence and anomalies |
| Classifier Agent | Infer incident category & severity |
| Timeline Agent | Build incident chronology |
| RCA Agent | Perform root cause analysis |
| Remediation Agent | Suggest safe recovery actions |
| Critic Agent | Validate reasoning & reduce hallucinations |
| Notification Agent | Generate stakeholder updates |
| Ticket Agent | Create incident ticket previews |

---

## 🎯 Supported Incident Categories

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

---

## 🧠 Why IncidentIQ is Different

Unlike toy demos or rule-only systems, IncidentIQ:

- Works on mixed, noisy, unlabeled production-style logs
- Separates deterministic evidence extraction from LLM reasoning
- Supports evidence-backed RCA instead of keyword guessing
- Includes human approval gates before external actions
- Uses hidden ground-truth evaluation pipelines
- Is designed for extensibility into enterprise DevOps ecosystems

---

## 🛠 Tech Stack

### Current MVP
- Python 3.11+
- LangGraph
- LangChain
- OpenAI / OpenRouter-compatible LLMs
- Pandas
- Pydantic
- FAISS / Chroma
- Streamlit / Colab

### Planned Production Stack
- FastAPI
- React Frontend
- PostgreSQL
- Vector Database
- OpenTelemetry / Prometheus / Grafana
- Slack / Teams / GitHub / JIRA Integrations

---

## 📁 Repository Structure

```text
IncidentIQ/
│
├── datasets/      # Synthetic mixed production-style incident datasets
├── docs/          # Architecture diagrams, screenshots, design notes, demo assets
├── notebooks/     # Experimental Colab/Jupyter prototypes and workflow validation
├── src/           # Main production-oriented source code
│
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

---

## Folder Details

### `datasets/`

Contains:
- raw mixed production-style logs
- hidden ground-truth evaluation datasets
- benchmark incident corpora

Purpose:
- evaluation
- testing
- demo scenarios
- workflow validation

---

### `docs/`

Contains:
- architecture diagrams
- LangGraph workflow diagrams
- screenshots
- design documents
- demo assets
- operational notes

---

### `notebooks/`

Contains:
- experimental Colab notebooks
- prompt engineering workflows
- prototype pipelines
- orchestration validation experiments

Important:
These notebooks are intended for:
- experimentation
- rapid prototyping
- team collaboration

The long-term maintainable implementation lives under:

```text
src/
```

---

### `src/`

Contains the modular production-oriented implementation.

Includes:
- LangGraph orchestration
- agents
- ingestion pipelines
- signal extraction
- clustering
- evaluation
- reporting
- RAG support

For detailed source architecture and planned implementation files, see:

```text
src/README.md
```
---

## 📊 Example Output

### Incident Detection
```text
Category: Database
Severity: P1
Likely Cause: Connection pool exhaustion
Affected Services: payment-api, postgres-primary
Confidence: 0.86
```

### Suggested Remediation
```text
- Check active DB sessions
- Identify long-running transactions
- Validate lock contention
- Scale application cautiously after DB capacity verification
```

---

## 🚀 Future Roadmap

- Advanced vector-based RAG retrieval
- Real-time streaming incident analysis
- OpenTelemetry trace correlation
- Service dependency graphs
- Live Slack/JIRA integrations
- Autonomous remediation approvals
- Kubernetes & cloud-native integrations

---

## 🧪 Ideal Use Cases

- DevOps Incident Triage
- SRE Operational Intelligence
- Production Outage Analysis
- Automated Postmortems
- AI-assisted On-call Support
- Root Cause Investigation
- Incident Knowledge Management

---

## Run The Final App

The production-runnable entry point is now `app.py`, backed by the reusable `src` pipeline.

```bash
python3 -m pip install -r requirements.txt
python3 -B app.py
```

Then open the local Gradio URL shown in the terminal, usually:

```text
http://127.0.0.1:7860
```

Run the smoke test with the bundled sample ZIP:

```bash
python3 -B scripts/smoke_test.py
```

The app is safe by default:

- RAG uses local runbooks under `src/rag/knowledge_base`.
- Slack/JIRA payloads are preview-only.
- Hidden `ground_truth_eval_only` files are skipped during runtime and used only after inference for scoring.
- Optional FAISS ingestion is available through `from src.rag import ingest`, but the default retrieval path works without paid APIs.

---

## 🏁 Vision

Upload raw production logs.  
Let AI agents infer what happened.  
Every conclusion is evidence-backed.  
Root causes are separated from symptoms.  
Remediation is safe, explainable, and approval-gated.

IncidentIQ becomes your AI-powered Incident Commander.

---

## 📌 Project Status

🚧 Active Development / Hackathon Prototype  
🔬 Experimental AI + DevOps Research Platform  
⚡ LangGraph-based Multi-Agent Incident Intelligence System
