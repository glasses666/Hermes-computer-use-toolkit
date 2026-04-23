from computer_use_toolkit.queue.actions import build_pending_pointer_action, payload_action_identity



def test_build_pending_pointer_action_adds_identity_and_fields():
    payload = build_pending_pointer_action("click", x=10, y=20, button="left", optional=None)
    assert payload["action_id"].startswith("ptr-")
    assert payload["action_type"] == "click"
    assert payload["x"] == 10
    assert payload["y"] == 20
    assert payload["button"] == "left"
    assert "optional" not in payload



def test_payload_action_identity_requires_both_fields():
    assert payload_action_identity({"action_id": "ptr-1", "action_type": "drag"}) == ("ptr-1", "drag")
    assert payload_action_identity({"action_id": "ptr-1"}) is None
    assert payload_action_identity({"action_type": "drag"}) is None
