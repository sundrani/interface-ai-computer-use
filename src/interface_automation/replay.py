from __future__ import annotations
import re
from pathlib import Path
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from .handoff import HandoffController
from .logging_utils import EvidenceLogger
from .models import CapabilityArtifact, RunResult, RunStatus, ActionType
from .policy import GuardrailPolicy, PolicyViolation
from .surface import BrowserSurface

TEMPLATE = re.compile(r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}")

def render(value: str | None, params: dict) -> str | None:
    if value is None: return None
    return TEMPLATE.sub(lambda m: str(params[m.group(1)]), value)

def classify_body(step, body: str):
    for rule in step.error_rules:
        if rule.match_text.lower() in body.lower():
            return rule
    return None

def replay(artifact: CapabilityArtifact, params: dict, evidence_dir: Path, headless: bool = False, allow_risky: bool = False) -> RunResult:
    logger = EvidenceLogger(evidence_dir)
    policy = GuardrailPolicy(allow_risky=allow_risky)
    policy.check_url(artifact.entry_url)
    missing = [p.name for p in artifact.inputs if p.required and p.name not in params]
    if missing:
        return RunResult(status=RunStatus.FAILURE, capability_id=artifact.capability_id, message=f"Missing inputs: {missing}")
    with BrowserSurface(headless=headless) as surface:
        surface.start_trace(); surface.goto(artifact.entry_url)
        try:
            for step in artifact.steps:
                logger.emit("step_start", step_id=step.id, action=step.action.value)
                try:
                    policy.check_step(step)
                except PolicyViolation as e:
                    surface.screenshot(evidence_dir / "failure.png")
                    logger.emit("policy_block", step_id=step.id, reason=str(e))
                    handoff = HandoffController(evidence_dir)
                    handoff.request({"reason": str(e), "step": step.id, "capability": artifact.capability_id})
                    if not headless and handoff.wait():
                        logger.emit("human_resume", step_id=step.id)
                        continue
                    return RunResult(status=RunStatus.ESCALATED, capability_id=artifact.capability_id, failed_step_id=step.id, message=str(e), evidence_dir=str(evidence_dir))

                value = render(step.value_template, params)
                retries = 0
                while True:
                    try:
                        if step.action == ActionType.CLICK: surface.click(step.target, step.timeout_ms)
                        elif step.action == ActionType.FILL: surface.fill(step.target, value or "", step.timeout_ms)
                        elif step.action == ActionType.READ:
                            out = surface.read(step.target, step.timeout_ms)
                            params.setdefault("__outputs__", {})[step.output_name or step.id] = out
                        elif step.action == ActionType.WAIT and step.wait_for_text:
                            surface.page.get_by_text(step.wait_for_text).wait_for(timeout=step.timeout_ms)
                        body = surface.body_text()
                        rule = classify_body(step, body)
                        if rule:
                            logger.emit("runtime_condition", step_id=step.id, code=rule.code, classification=rule.classification)
                            if rule.classification == "business_outcome":
                                return RunResult(status=RunStatus.BUSINESS_OUTCOME, capability_id=artifact.capability_id, outcome_code=rule.code, message=rule.match_text, evidence_dir=str(evidence_dir))
                            if rule.classification == "recoverable" and retries < rule.max_retries:
                                retries += 1; surface.page.reload(wait_until="domcontentloaded"); continue
                            if rule.action == "escalate":
                                surface.screenshot(evidence_dir / "failure.png")
                                return RunResult(status=RunStatus.ESCALATED, capability_id=artifact.capability_id, failed_step_id=step.id, message=rule.code, evidence_dir=str(evidence_dir))
                            return RunResult(status=RunStatus.FAILURE, capability_id=artifact.capability_id, failed_step_id=step.id, message=rule.code, evidence_dir=str(evidence_dir))
                        if step.checkpoint_text and step.checkpoint_text.lower() not in body.lower():
                            raise RuntimeError(f"Checkpoint missing: {step.checkpoint_text}")
                        break
                    except (PlaywrightTimeoutError, RuntimeError) as e:
                        surface.screenshot(evidence_dir / "failure.png")
                        logger.emit("step_failure", step_id=step.id, error=str(e), observed=surface.body_text()[:500])
                        return RunResult(status=RunStatus.FAILURE, capability_id=artifact.capability_id, failed_step_id=step.id, message=str(e), observed=surface.body_text()[:500], evidence_dir=str(evidence_dir))
                logger.emit("step_success", step_id=step.id)

            body = surface.body_text()
            if artifact.success_checkpoint and artifact.success_checkpoint.lower() not in body.lower():
                surface.screenshot(evidence_dir / "failure.png")
                return RunResult(status=RunStatus.FAILURE, capability_id=artifact.capability_id, message="Final checkpoint not satisfied", observed=body[:500], evidence_dir=str(evidence_dir))
            surface.screenshot(evidence_dir / "success.png")
            outputs = params.get("__outputs__", {})
            logger.emit("run_success", outputs=outputs)
            return RunResult(status=RunStatus.SUCCESS, capability_id=artifact.capability_id, outputs=outputs, evidence_dir=str(evidence_dir))
        finally:
            surface.stop_trace(evidence_dir / "trace.zip")
