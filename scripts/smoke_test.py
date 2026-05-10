import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import analyze_uploaded_logs


def main() -> None:
    sample = Path("datasets/incidentiq_small_test_sample_easy.zip")
    if not sample.exists():
        raise FileNotFoundError(f"Missing smoke-test sample: {sample}")

    response = analyze_uploaded_logs(
        [str(sample)],
        options={
            "enable_rag": True,
            "run_evals": True,
            "max_clusters": 25,
            "max_evidence_per_cluster": 25,
            "preview_only": True,
        },
    )

    assert response.status == "completed", response.errors
    assert response.summary["events_parsed"] > 0, response.summary
    assert response.summary["signals_found"] > 0, response.summary
    assert response.summary["incidents_found"] > 0, response.summary
    assert response.reports.get("output_zip") and Path(response.reports["output_zip"]).exists(), response.reports
    assert response.incidents[0].root_cause.get("supporting_evidence"), "Top incident has no evidence"

    print(
        json.dumps(
            {
                "run_id": response.run_id,
                "status": response.status,
                "highest_severity": response.highest_severity,
                "summary": response.summary,
                "eval": response.eval.get("summary"),
                "reports": response.reports,
                "top_incidents": [
                    {
                        "severity": incident.severity,
                        "category": incident.category,
                        "title": incident.title,
                    }
                    for incident in response.incidents[:5]
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
