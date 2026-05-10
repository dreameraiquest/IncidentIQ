# Block 2 - Full Raw Mixed DevOps Logs

The `raw_logs/` files are blind runtime inputs and do not contain category, scenario, severity, or remediation labels.

Use `ground_truth_eval_only/` only after inference to score the LangGraph output.

Files are mixed by time window, not by category, to mimic production log bundles.
