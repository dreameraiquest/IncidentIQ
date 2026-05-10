import hashlib
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any, Tuple
from src.models.incident import SignalMatch, EvidenceCluster
from src.utils.time_utils import strongest_severity

def build_evidence_clusters(signals: List[SignalMatch], options: Dict[str, Any], severity_order: Dict[str, int]) -> List[EvidenceCluster]:
    grouped: Dict[Tuple[str, str, str], List[SignalMatch]] = defaultdict(list)
    for sig in signals:
        source_bucket = Path(sig.source_file).name
        grouped[(sig.signal_type, source_bucket, sig.signature)].append(sig)

    max_evidence = int(options.get("max_evidence_per_cluster", 25))
    clusters = []
    for (category, source_bucket, signature), items in grouped.items():
        items = sorted(items, key=lambda x: (x.timestamp or "", x.source_file, x.line_no))
        total_weight = sum(i.weight for i in items)
        if total_weight < 2.0 and category != "Unknown":
            continue
        
        sev = strongest_severity((i.severity_hint for i in items), severity_order)
        services = sorted({i.service for i in items if i.service}) or [source_bucket]
        traces = sorted({str(i.trace_id) for i in items if i.trace_id})[:20]
        
        # Convert models to dict for clustering storage
        evidence = [i.model_dump() if hasattr(i, "model_dump") else i.dict() for i in items[:max_evidence]]
        
        raw_key = f"{category}|{source_bucket}|{signature}|{items[0].source_file}|{items[0].line_no}"
        cluster_id = "cluster_" + hashlib.sha1(raw_key.encode()).hexdigest()[:10]
        
        clusters.append(
            EvidenceCluster(
                cluster_id=cluster_id,
                candidate_category=category,
                signature=signature,
                affected_services=services,
                start_ts=items[0].timestamp,
                end_ts=items[-1].timestamp,
                window="all-window",
                signal_count=len(items),
                total_weight=round(total_weight, 2),
                severity_hint=sev,
                evidence=evidence,
                rule_ids=sorted({i.rule_id for i in items}),
                trace_ids=traces,
                summary=f"{category} signals for {', '.join(services[:4])}; signature={signature}; evidence={len(items)}.",
            )
        )
    clusters.sort(key=lambda c: (severity_order.get(c.severity_hint, 5), -c.total_weight, c.candidate_category))
    return clusters[: int(options.get("max_clusters", 25) or 25)]
