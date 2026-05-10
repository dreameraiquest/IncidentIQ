---
title: IncidentIQ
emoji: "🚨"
colorFrom: blue
colorTo: indigo
sdk: gradio
app_file: app.py
python_version: "3.11"
suggested_hardware: cpu-basic
fullWidth: true
header: default
short_description: Multi-agent DevOps incident analysis with evidence-backed RCA and safe remediation previews.
---

# IncidentIQ

IncidentIQ turns uploaded DevOps logs into incident candidates, timelines, root cause analysis, remediation guidance, preview Jira tickets, and preview Slack updates.

This Space is deployed from GitHub via GitHub Actions.

## Notes

- Upload `.zip`, `.jsonl`, `.log`, `.txt`, or `.json` files.
- Runtime analysis never uses hidden eval labels unless you explicitly upload ground-truth files and enable evals.
- External integrations remain preview-only unless you intentionally reconfigure them.
