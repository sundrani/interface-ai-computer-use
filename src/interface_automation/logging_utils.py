from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from .redaction import redact

class EvidenceLogger:
    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "events.jsonl"

    def emit(self, event: str, **payload):
        record = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **payload}
        safe = redact(json.dumps(record, default=str))
        with self.path.open("a", encoding="utf-8") as f:
            f.write(safe + "\n")
