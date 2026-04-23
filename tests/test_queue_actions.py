from computer_use_toolkit.queue.actions import (
    build_pending_pointer_action,
    payload_action_identity,
    record_pending_pointer_action,
)



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



def test_record_pending_pointer_action_sets_pending_payload_and_clears_claim_state_without_mutating_input():
    session = {
        "app_session_id": "app-1",
        "pending_pointer_action": {"action_id": "ptr-old", "action_type": "click"},
        "pending_pointer_claim_token": "claim-old",
        "last_pointer_action_result": {"status": "completed"},
    }

    updated = record_pending_pointer_action(session, "scroll", x=10, y=20, delta_y=-120, optional=None)

    assert updated["pending_pointer_action"]["action_id"].startswith("ptr-")
    assert updated["pending_pointer_action"]["action_type"] == "scroll"
    assert updated["pending_pointer_action"]["x"] == 10
    assert updated["pending_pointer_action"]["y"] == 20
    assert updated["pending_pointer_action"]["delta_y"] == -120
    assert "optional" not in updated["pending_pointer_action"]
    assert updated["pending_pointer_claim_token"] == ""
    assert updated["last_pointer_action_result"] is None
    assert session == {
        "app_session_id": "app-1",
        "pending_pointer_action": {"action_id": "ptr-old", "action_type": "click"},
        "pending_pointer_claim_token": "claim-old",
        "last_pointer_action_result": {"status": "completed"},
    }
