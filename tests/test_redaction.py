from interface_automation.redaction import redact

def test_redacts_nine_digit_identifier():
    assert "123456789" not in redact("ssn 123456789")
