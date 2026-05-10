import re
from datetime import datetime, timezone
from typing import Any, Optional
from dateutil import parser as dtparser

def parse_timestamp(value: Any) -> Optional[str]:
    if value in (None, "", "null"):
        return None
    try:
        return dtparser.parse(str(value)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except Exception:
        return None

def strongest_severity(severities: list[str], severity_order: dict[str, int]) -> str:
    vals = [s if s in severity_order else "UNKNOWN" for s in severities]
    return min(vals or ["UNKNOWN"], key=lambda x: severity_order[x])
