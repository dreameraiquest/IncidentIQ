from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class LogEvent(BaseModel):
    source_file: str
    line_no: int
    timestamp: Optional[str] = None
    level: str = "UNKNOWN"
    service: str = "unknown"
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    host: Optional[str] = None
    namespace: Optional[str] = None
    pod: Optional[str] = None
    container: Optional[str] = None
    raw_line: str
    parse_status: str = "parsed"
    metadata: Dict[str, Any] = Field(default_factory=dict)
