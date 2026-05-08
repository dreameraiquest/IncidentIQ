# IncidentIQ 🚨
## Multi-Agent AI Platform for DevOps Incident Detection, RCA & Automated Response

IncidentIQ is an AI-powered multi-agent DevOps incident analysis platform that transforms raw production logs into evidence-backed incident intelligence, root cause analysis (RCA), remediation guidance, and operational action plans.

Built using LangGraph, LLMs, and deterministic evidence extraction pipelines, IncidentIQ acts like an AI Incident Commander for SRE and DevOps teams. The system ingests noisy, mixed, production-style logs and orchestrates specialized agents to detect incidents, infer severity, reconstruct timelines, identify probable root causes, recommend safe remediation actions, and generate collaboration-ready outputs such as Slack alerts and GitHub/JIRA ticket previews.

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
