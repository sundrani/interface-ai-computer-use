from __future__ import annotations
from urllib.parse import urlparse
from .models import ActionType, Risk, Step

class PolicyViolation(RuntimeError):
    pass

class GuardrailPolicy:
    def __init__(self, allowed_hosts: set[str] | None = None, allow_risky: bool = False):
        self.allowed_hosts = allowed_hosts or {"127.0.0.1", "localhost"}
        self.allowed_actions = {ActionType.NAVIGATE, ActionType.CLICK, ActionType.FILL, ActionType.READ, ActionType.WAIT}
        self.allow_risky = allow_risky

    def check_url(self, url: str) -> None:
        host = urlparse(url).hostname
        if host not in self.allowed_hosts:
            raise PolicyViolation(f"Host {host!r} is not allowlisted")

    def check_step(self, step: Step) -> None:
        if step.action not in self.allowed_actions:
            raise PolicyViolation(f"Action {step.action} is not allowlisted")
        if step.risk == Risk.RISKY and not self.allow_risky:
            raise PolicyViolation("Risky action requires human approval")
