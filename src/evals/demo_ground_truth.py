import json
from pathlib import Path
from typing import Any, Dict, List


def load_demo_ground_truth_easy() -> List[Dict[str, Any]]:
    path = Path(__file__).with_name("demo_ground_truth_easy.json")
    return json.loads(path.read_text(encoding="utf-8"))