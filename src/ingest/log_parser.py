import json
import re
from typing import Optional
from src.models.log_event import LogEvent
from src.utils.time_utils import parse_timestamp

def parse_log_line(line: str, source_file: str, line_no: int) -> LogEvent:
    raw = line.rstrip("\n")
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            msg = obj.get("message") or obj.get("msg") or obj.get("log") or obj.get("event") or raw
            return LogEvent(
                source_file=source_file,
                line_no=line_no,
                timestamp=parse_timestamp(obj.get("ts") or obj.get("timestamp") or obj.get("time") or obj.get("@timestamp")),
                level=str(obj.get("level") or obj.get("severity") or obj.get("log_level") or "UNKNOWN").upper(),
                service=str(obj.get("service") or obj.get("app") or obj.get("logger") or obj.get("component") or obj.get("pod") or "unknown"),
                message=str(msg),
                trace_id=obj.get("trace_id") or obj.get("traceId") or obj.get("correlation_id") or obj.get("request_id"),
                span_id=obj.get("span_id") or obj.get("spanId"),
                host=obj.get("host"),
                namespace=obj.get("namespace"),
                pod=obj.get("pod"),
                container=obj.get("container"),
                raw_line=raw,
                metadata={k: v for k, v in obj.items() if k not in {"message", "msg", "log"}},
            )
    except Exception:
        pass

    ts = None
    m_ts = re.search(r"(20\d{2}-\d{2}-\d{2}[T ][0-9:.+-]+Z?)", raw)
    if m_ts:
        ts = parse_timestamp(m_ts.group(1))
    
    m_level = re.search(r"\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b", raw, re.I)
    level = (m_level.group(1).upper() if m_level else "UNKNOWN").replace("WARNING", "WARN")
    
    m_service = re.search(r"(?:service|app|component|pod)=([A-Za-z0-9_.-]+)", raw)
    service = m_service.group(1) if m_service else "unknown"
    
    return LogEvent(source_file=source_file, line_no=line_no, timestamp=ts, level=level, service=service, message=raw, raw_line=raw, parse_status="text")
