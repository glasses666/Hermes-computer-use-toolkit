import json

from computer_use_toolkit.state import manifests as manifest_state
from computer_use_toolkit.state.manifests import find_pending_session_manifest, list_pending_session_manifests, pending_action_identity
from computer_use_toolkit.state.session_store import InvalidSessionID, session_manifest_path, session_state_root, validate_session_id



def _write_manifest(root, app_session_id, payload):
    path = session_manifest_path(root, app_session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path



def test_session_helpers_validate_ids_and_paths(tmp_path):
    root = session_state_root(tmp_path)
    assert root == tmp_path / "computer-use" / "session-state"
    assert validate_session_id("app-123") == "app-123"
    assert session_manifest_path(root, "app-123") == root / "app-123.json"



def test_session_helpers_reject_traversal_and_drive_like_ids(tmp_path):
    root = session_state_root(tmp_path)
    for bad in ["", "../escape", "..", "C:escape", "slash/name", "back\\name"]:
        try:
            session_manifest_path(root, bad)
        except InvalidSessionID:
            pass
        else:
            raise AssertionError(f"expected InvalidSessionID for {bad!r}")



def test_pending_action_identity_requires_manifest_style_payload():
    assert pending_action_identity({"pending_pointer_action": {"action_id": "ptr-1", "action_type": "click"}}) == ("ptr-1", "click")
    assert pending_action_identity({"pending_pointer_action": {"action_id": "ptr-1"}}) is None
    assert pending_action_identity({"action_id": "ptr-1", "action_type": "click"}) is None



def test_list_pending_session_manifests_filters_malformed_and_mismatched_payloads(tmp_path):
    root = session_state_root(tmp_path)
    _write_manifest(root, "app-good", {
        "app_session_id": "app-good",
        "pending_pointer_action": {"action_id": "ptr-1", "action_type": "click"},
    })
    _write_manifest(root, "app-missing-action", {
        "app_session_id": "app-missing-action",
        "pending_pointer_action": {"action_id": "ptr-2"},
    })
    _write_manifest(root, "app-mismatch", {
        "app_session_id": "different-id",
        "pending_pointer_action": {"action_id": "ptr-3", "action_type": "drag"},
    })

    manifests = list_pending_session_manifests(root)
    assert manifests == [{
        "app_session_id": "app-good",
        "pending_pointer_action": {"action_id": "ptr-1", "action_type": "click"},
    }]



def test_list_pending_session_manifests_rejects_symlinked_manifest_that_escapes_root(tmp_path):
    root = session_state_root(tmp_path)
    root.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside-manifest.json"
    outside.write_text(
        json.dumps(
            {
                "app_session_id": "app-link",
                "pending_pointer_action": {"action_id": "ptr-link", "action_type": "click"},
            }
        ),
        encoding="utf-8",
    )
    (root / "app-link.json").symlink_to(outside)

    assert list_pending_session_manifests(root) == []



def test_list_pending_session_manifests_reads_resolved_path_after_symlink_check(tmp_path, monkeypatch):
    root = session_state_root(tmp_path)
    root.mkdir(parents=True, exist_ok=True)
    inside = root / "inside.json"
    inside.write_text(
        json.dumps(
            {
                "app_session_id": "inside",
                "pending_pointer_action": {"action_id": "ptr-inside", "action_type": "click"},
            }
        ),
        encoding="utf-8",
    )
    outside = tmp_path / "outside-manifest.json"
    outside.write_text(
        json.dumps(
            {
                "app_session_id": "app-link",
                "pending_pointer_action": {"action_id": "ptr-link", "action_type": "click"},
            }
        ),
        encoding="utf-8",
    )
    link = root / "app-link.json"
    link.symlink_to(inside)

    original_load_manifest = manifest_state.load_manifest

    def swapping_load_manifest(path):
        link.unlink()
        link.symlink_to(outside)
        return original_load_manifest(path)

    monkeypatch.setattr(manifest_state, "load_manifest", swapping_load_manifest)

    assert list_pending_session_manifests(root) == [
        {
            "app_session_id": "inside",
            "pending_pointer_action": {"action_id": "ptr-inside", "action_type": "click"},
        }
    ]



def test_find_pending_session_manifest_honors_action_id(tmp_path):
    root = session_state_root(tmp_path)
    _write_manifest(root, "app-1", {
        "app_session_id": "app-1",
        "pending_pointer_action": {"action_id": "ptr-1", "action_type": "scroll"},
    })
    assert find_pending_session_manifest(root, "app-1", "ptr-1")["app_session_id"] == "app-1"
    assert find_pending_session_manifest(root, "app-1", "ptr-2") is None
