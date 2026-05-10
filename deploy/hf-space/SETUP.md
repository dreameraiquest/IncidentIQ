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

## 4. Triggering deploys

- Push to `main` with changes to `app.py`, `src/`, `deploy/hf-space/`, or the workflow file.
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
