from __future__ import annotations
import re

PATTERNS = [
    (re.compile(r"(?i)(authorization:\s*bearer\s+)[A-Za-z0-9._-]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)\S+"), r"\1[REDACTED]"),
    (re.compile(r"\b\d{9}\b"), "[REDACTED-9DIGIT]"),
]

def redact(text: str) -> str:
    out = text
    for pattern, repl in PATTERNS:
        out = pattern.sub(repl, out)
    return out
