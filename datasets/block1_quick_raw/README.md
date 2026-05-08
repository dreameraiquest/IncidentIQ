# Block 1 - Quick Raw Mixed DevOps Logs

This dataset is intentionally realistic for agent testing.

## Important
The files in `raw_logs/` are blind runtime inputs. They do NOT contain:
- category
- scenario name
- scenario id
- severity hint
- remediation hint

Your LangGraph app should infer incident category, severity, root cause, evidence, and remediation from raw operational signals.

## Folder layout
- `raw_logs/` → give these to the app.
- `ground_truth_eval_only/` → use only after inference to score results.
- `manifest.json` → dataset metadata.

## Why files are mixed
The raw logs are not separated into database/network/auth folders because real production logs arrive as mixed service/time windows.
Each file contains normal logs, noise, warnings, errors, and overlapping signals.
