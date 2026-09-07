from __future__ import annotations
import re
import uuid
from .models import AgentDecision, CapabilityArtifact, LocatorStrategy, OutputSpec, ParameterSpec, Step, ActionType, ErrorRule

PARAM_RE = re.compile(r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}")

def decision_to_step(index: int, d: AgentDecision) -> Step:
    target = None
    if d.role and d.name:
        target = LocatorStrategy(kind="role_name", role=d.role, name=d.name)
    action = ActionType(d.action)
    errors = [
        ErrorRule(code="NOT_FOUND", classification="business_outcome", match_text="No member found", action="return"),
        ErrorRule(code="PERMISSION_DENIED", classification="hard_failure", match_text="Permission denied", action="escalate"),
        ErrorRule(code="SESSION_EXPIRED", classification="recoverable", match_text="Session expired", action="retry", max_retries=1),
    ]
    return Step(
        id=f"s{index:02d}", action=action, target=target, value_template=d.value,
        output_name=d.output_name, risk=d.risk, checkpoint_text=d.checkpoint_text,
        error_rules=errors,
    )

def build_artifact(goal: str, entry_url: str, target_app: str, decisions: list[AgentDecision]) -> CapabilityArtifact:
    steps: list[Step] = []
    params: dict[str, ParameterSpec] = {}
    outputs: list[OutputSpec] = []
    success = ""
    step_no = 1
    for d in decisions:
        if d.action in {"done", "escalate"}:
            if d.checkpoint_text:
                success = d.checkpoint_text
            continue
        step = decision_to_step(step_no, d)
        step_no += 1
        if step.value_template:
            for p in PARAM_RE.findall(step.value_template):
                params.setdefault(p, ParameterSpec(name=p, description=f"Runtime value for {p}"))
        if step.output_name:
            outputs.append(OutputSpec(name=step.output_name, source_step_id=step.id))
        steps.append(step)
    if not success:
        success = decisions[-1].checkpoint_text if decisions and decisions[-1].checkpoint_text else ""
    return CapabilityArtifact(
        capability_id=f"cap_{uuid.uuid4().hex[:10]}",
        name="discovered_capability",
        description=goal,
        target_app=target_app,
        entry_url=entry_url,
        inputs=list(params.values()), outputs=outputs, steps=steps,
        success_checkpoint=success,
    )
