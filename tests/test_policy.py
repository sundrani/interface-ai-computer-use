import pytest
from interface_automation.models import Step, ActionType, Risk
from interface_automation.policy import GuardrailPolicy, PolicyViolation

def test_blocks_non_allowlisted_host():
    with pytest.raises(PolicyViolation): GuardrailPolicy().check_url("https://example.com")

def test_blocks_risky_by_default():
    with pytest.raises(PolicyViolation): GuardrailPolicy().check_step(Step(id="s1", action=ActionType.CLICK, risk=Risk.RISKY))
