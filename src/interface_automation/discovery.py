from __future__ import annotations
import json
from pathlib import Path
from .llm import LLMPlanner
from .logging_utils import EvidenceLogger
from .models import AgentDecision, Risk
from .policy import GuardrailPolicy, PolicyViolation
from .recorder import build_artifact
from .surface import BrowserSurface


def discover(goal: str, url: str, artifact_path: Path, evidence_dir: Path, headless: bool = False, max_steps: int = 15):
    policy = GuardrailPolicy(allow_risky=False)
    policy.check_url(url)
    planner = LLMPlanner()
    logger = EvidenceLogger(evidence_dir)
    history: list[dict] = []
    decisions: list[AgentDecision] = []
    with BrowserSurface(headless=headless) as surface:
        surface.start_trace(); surface.goto(url)
        try:
            for i in range(max_steps):
                snapshot = surface.observe()
                (evidence_dir / f"snapshot_{i:02d}.txt").write_text(snapshot, encoding="utf-8")
                decision = planner.decide(goal, snapshot, history)
                logger.emit("agent_decision", step=i, decision=decision.model_dump())
                decisions.append(decision)
                if decision.action == "done":
                    artifact = build_artifact(goal, url, "legacy-bank-demo", decisions)
                    artifact.discovery_evidence = str(evidence_dir)
                    artifact_path.parent.mkdir(parents=True, exist_ok=True)
                    artifact_path.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
                    surface.screenshot(evidence_dir / "success.png")
                    return artifact
                if decision.action == "escalate":
                    raise RuntimeError(f"Discovery escalated: {decision.reason}")
                if decision.risk == Risk.RISKY:
                    raise PolicyViolation("Discovery attempted risky action; requires human approval")
                spec = None
                if decision.role and decision.name:
                    from .models import LocatorStrategy
                    spec = LocatorStrategy(kind="role_name", role=decision.role, name=decision.name)
                if decision.action == "click": surface.click(spec)
                elif decision.action == "fill": surface.fill(spec, decision.value or "")
                elif decision.action == "read":
                    value = surface.read(spec)
                    history.append({"action": "read", "target": decision.name, "value": value})
                    continue
                elif decision.action == "wait" and decision.checkpoint_text:
                    surface.page.get_by_text(decision.checkpoint_text).wait_for(timeout=5000)
                history.append(decision.model_dump())
            raise RuntimeError("Discovery max-steps exceeded")
        except Exception:
            surface.screenshot(evidence_dir / "failure.png")
            raise
        finally:
            surface.stop_trace(evidence_dir / "trace.zip")
