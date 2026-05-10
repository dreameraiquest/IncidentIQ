# Hugging Face Space CI/CD Setup

This repo includes a GitHub Actions workflow that assembles a Space bundle from the root `app.py`, root `requirements.txt`, and the full `src/` package, then force-pushes it to a Hugging Face Space.

## 1. Create the Space

- Create a Hugging Face Space with SDK `Gradio`.
- Copy the repo id, for example `your-username/incidentiq`.

## 2. Add GitHub credentials

Add these in your GitHub repository settings:

- Secret: `HF_TOKEN`
  - Use a fine-grained Hugging Face token with write access to the target Space.
- Variable: `HF_SPACE_REPO_ID`
  - Example: `your-username/incidentiq`

## 3. Recommended Space variables

Set these in the Hugging Face Space Settings UI:

```text
INCIDENTIQ_WORK_ROOT=/tmp/incidentiq_work
ENABLE_LLM_MODE=false
ENABLE_RAG_MODE=true
ENABLE_EVAL_MODE=false
ENABLE_PREVIEW_MODE=true
ENABLE_REAL_INTEGRATIONS=false
GRADIO_ANALYTICS_ENABLED=false
INCIDENTIQ_RAG_TOP_K=5
JIRA_BASE_URL=https://jira.example.com
JIRA_PROJECT_KEY=OPS
```

Do not use local machine paths such as `/Users/...` in Hugging Face. Use these cloud-safe values instead:

```text
INCIDENTIQ_WORK_ROOT=/tmp/incidentiq_work
workDir=src/rag
GRADIO_SERVER_NAME=0.0.0.0
```

You can omit `PORT` on Hugging Face because the Space runtime manages the public port for Gradio.

Add these as Hugging Face Space **Secrets** when you want LLM judging and observability:

```text
OPENROUTER_API_KEY=<rotated-openrouter-key>
OPENAI_API_KEY=<rotated-openrouter-or-openai-key>
LANGSMITH_API_KEY=<rotated-langsmith-key>
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=incidentiq
```

Add these as Hugging Face Space **Variables** for Jira preview labels:

```text
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_PROJECT_KEY=<project-key>
SLACK_CHANNEL=#devops-incidents
```

Add these as Hugging Face Space **Secrets** when you want real n8n dispatch:

```text
SLACK_WEBHOOK_URL=https://your-n8n-host/webhook/slack...
JIRA_WEBHOOK_URL=https://your-n8n-host/webhook/jira...
```

`SLACK_WEBHOOK_URL` can also be a direct Slack Incoming Webhook URL (`https://hooks.slack.com/...`). `JIRA_WEBHOOK_URL` should be an n8n webhook or a Jira Automation incoming webhook that accepts JSON.

Alias names are also supported:

```text
N8N_SLACK_WEBHOOK_URL=https://your-n8n-host/webhook/slack...
N8N_JIRA_WEBHOOK_URL=https://your-n8n-host/webhook/jira...
```

After changing Space secrets, restart the Space from Hugging Face Settings so the running app picks up the new environment.

Important: if any API key or token was shared in chat, screenshots, commits, or logs, rotate it before deploying.

## 4. Triggering deploys

- Push to the GitHub `deploy` branch with changes to `app.py`, `requirements.txt`, `src/`, `deploy/hf-space/`, or the workflow file.
- Or trigger the workflow manually from the GitHub Actions tab.

## 5. Local bundle preview

You can build the exact bundle that the workflow deploys:

```bash
python3 scripts/build_hf_space_bundle.py
```

The generated bundle will be written to:

```text
.hf-space-build/
```

The deploy bundle intentionally uses the root app and requirements files so the Hugging Face Space receives the same UI and dependency changes that are committed to the main repo.

The prebuilt FAISS index under `src/rag/faiss_index/` is intentionally excluded from the Space bundle because Hugging Face rejects binary files unless Xet storage is configured. Runtime RAG still receives the text knowledge base under `src/rag/knowledge_base/`.
