from __future__ import annotations
import json
import os
from openai import OpenAI
from .models import AgentDecision

SYSTEM = """You are a computer-use discovery planner. You receive a goal and an accessibility snapshot.
Choose exactly ONE next action. Prefer accessible role/name targeting. Never invent controls absent from the snapshot.
Use fill for textboxes, click for buttons/links, read for extracting final data, done only when the goal and checkpoint are satisfied.
Classify risky/irreversible actions as risk='risky'. Return JSON only with keys:
action, role, name, value, output_name, checkpoint_text, risk, reason.
For read, role/name must identify the exact visible element. For wait, put visible text in checkpoint_text.
For done/escalate, role/name/value may be null."""

class LLMPlanner:
    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("CUA_MODEL", "gpt-5.6-luna")
        self.client = OpenAI()

    def decide(self, goal: str, snapshot: str, history: list[dict]) -> AgentDecision:
        prompt = f"GOAL:\n{goal}\n\nRECENT ACTIONS:\n{json.dumps(history[-8:])}\n\nCURRENT ACCESSIBILITY SNAPSHOT:\n{snapshot}\n"
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )
        text = response.output_text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
        return AgentDecision.model_validate_json(text)
