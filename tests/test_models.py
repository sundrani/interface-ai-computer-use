from interface_automation.models import CapabilityArtifact, ParameterSpec, OutputSpec, Step, ActionType, LocatorStrategy

def test_artifact_roundtrip():
    a = CapabilityArtifact(capability_id="c1", name="n", description="d", target_app="a", entry_url="http://127.0.0.1:8000", inputs=[ParameterSpec(name="member_id")], outputs=[OutputSpec(name="balance", source_step_id="s3")], steps=[Step(id="s1", action=ActionType.FILL, target=LocatorStrategy(kind="role_name", role="textbox", name="Member ID"), value_template="{{member_id}}")], success_checkpoint="Member Detail")
    assert CapabilityArtifact.model_validate_json(a.model_dump_json()).capability_id == "c1"
