from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field

class ActionType(str, Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    FILL = "fill"
    READ = "read"
    WAIT = "wait"

class Risk(str, Enum):
    SAFE = "safe"
    REVERSIBLE = "reversible"
    RISKY = "risky"

class LocatorStrategy(BaseModel):
    kind: Literal["role_name", "label", "text", "css"]
    role: str | None = None
    name: str | None = None
    value: str | None = None
    exact: bool = True

class ParameterSpec(BaseModel):
    name: str
    type: Literal["string", "integer", "number", "boolean"] = "string"
    required: bool = True
    sensitive: bool = False
    description: str = ""

class OutputSpec(BaseModel):
    name: str
    type: Literal["string", "integer", "number", "boolean"] = "string"
    source_step_id: str
    description: str = ""

class ErrorRule(BaseModel):
    code: str
    classification: Literal["business_outcome", "recoverable", "hard_failure"]
    match_text: str
    action: Literal["return", "retry", "escalate", "fail"]
    max_retries: int = 0

class Step(BaseModel):
    id: str
    action: ActionType
    target: LocatorStrategy | None = None
    value_template: str | None = None
    output_name: str | None = None
    wait_for_text: str | None = None
    risk: Risk = Risk.SAFE
    checkpoint_text: str | None = None
    timeout_ms: int = 5000
    error_rules: list[ErrorRule] = Field(default_factory=list)

class CapabilityArtifact(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    capability_id: str
    capability_version: int = 1
    name: str
    description: str
    target_app: str
    entry_url: str
    tenant_scope: str = "vendor-base"
    app_version_range: str = "demo-v1"
    inputs: list[ParameterSpec]
    outputs: list[OutputSpec]
    steps: list[Step]
    success_checkpoint: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    discovery_evidence: str | None = None

class RunStatus(str, Enum):
    SUCCESS = "success"
    BUSINESS_OUTCOME = "business_outcome"
    FAILURE = "failure"
    ESCALATED = "escalated"

class RunResult(BaseModel):
    status: RunStatus
    capability_id: str | None = None
    outputs: dict[str, Any] = Field(default_factory=dict)
    outcome_code: str | None = None
    failed_step_id: str | None = None
    message: str = ""
    observed: str | None = None
    evidence_dir: str | None = None

class AgentDecision(BaseModel):
    action: Literal["click", "fill", "read", "wait", "done", "escalate"]
    role: str | None = None
    name: str | None = None
    value: str | None = None
    output_name: str | None = None
    checkpoint_text: str | None = None
    risk: Risk = Risk.SAFE
    reason: str
