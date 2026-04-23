from computer_use_toolkit.worker.service import prioritize_pending_actions, requested_pending_actions



def _pending(app_session_id, action_id, action_type="click"):
    return {
        "app_session_id": app_session_id,
        "pending_pointer_action": {"action_id": action_id, "action_type": action_type},
    }



def test_prioritize_pending_actions_moves_requested_item_first():
    pending_actions = [_pending("app-1", "ptr-1"), _pending("app-2", "ptr-2")]
    ordered = prioritize_pending_actions(pending_actions, preferred_app_session_id="app-2", preferred_action_id="ptr-2")
    assert ordered[0]["app_session_id"] == "app-2"



def test_requested_pending_actions_returns_exact_matches_first():
    pending_actions = [_pending("app-1", "ptr-1"), _pending("app-2", "ptr-2")]
    matches = requested_pending_actions(pending_actions, preferred_app_session_id="app-2", preferred_action_id="ptr-2")
    assert matches == [_pending("app-2", "ptr-2")]



def test_requested_pending_actions_uses_manifest_fallback_only_when_identity_is_valid():
    pending_actions = [_pending("app-1", "ptr-1")]
    valid_manifest = _pending("app-2", "ptr-2", action_type="drag")
    invalid_manifest = {"app_session_id": "app-2", "pending_pointer_action": {"action_id": "ptr-2"}}

    assert requested_pending_actions(pending_actions, preferred_app_session_id="app-2", preferred_action_id="ptr-2", manifest_fallback=valid_manifest) == [valid_manifest]
    assert requested_pending_actions(pending_actions, preferred_app_session_id="app-2", preferred_action_id="ptr-2", manifest_fallback=invalid_manifest) == []
