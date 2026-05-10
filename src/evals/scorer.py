from typing import List, Dict, Any

def score_incident(detected: Dict[str, Any], ground_truth: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Step 7 of the Guide: Score the detected incident against hidden ground truth labels.
    """
    # Simple matching logic for the demo
    # In a real scenario, this would compare categories, severities, and timestamps
    matches = []
    for gt in ground_truth:
        if gt.get("category") == detected.get("category"):
            matches.append(gt)
            
    score = 1.0 if matches else 0.0
    return {
        "score": score,
        "matched_with": [m.get("id") for m in matches],
        "feedback": "Category match successful" if matches else "No matching ground truth found"
    }
