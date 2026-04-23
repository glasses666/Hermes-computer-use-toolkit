import json
from pathlib import Path

from computer_use_toolkit.state.approval_store import (
    approval_entry_label,
    approval_store_path,
    load_approval_entries,
    save_approval_entries,
)



def test_approval_store_path_uses_hermes_home(tmp_path):
    path = approval_store_path(tmp_path)
    assert path == tmp_path / "computer-use" / "ComputerUseAppApprovals.json"



def test_save_and_load_approval_entries_round_trip(tmp_path):
    path = approval_store_path(tmp_path)
    save_approval_entries(
        path,
        [
            {"approval_name": "Safari", "bundle_id": "com.apple.Safari", "bundle_path": "/Applications/Safari.app"},
            {"approval_name": "Safari", "bundle_id": "com.apple.Safari", "bundle_path": "/Applications/Safari.app"},
            {"approval_name": "Notes", "bundle_id": "com.example.notes", "bundle_path": "/Applications/Notes.app"},
        ],
    )
    entries = load_approval_entries(path)
    assert [approval_entry_label(entry) for entry in entries] == ["Notes", "Safari"]

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["approved_apps"] == ["Notes", "Safari"]
    assert len(payload["approved_app_entries"]) == 2



def test_load_approval_entries_uses_legacy_fallback_precedence(tmp_path):
    path = approval_store_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({
            "approved_apps": [],
            "approvedBundleIdentifiers": ["Safari", "Notes"],
        }),
        encoding="utf-8",
    )
    entries = load_approval_entries(path)
    assert [approval_entry_label(entry) for entry in entries] == ["Notes", "Safari"]



def test_load_approval_entries_handles_garbage_shapes_fail_closed(tmp_path):
    path = approval_store_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"approved_apps": "oops", "approvedBundleIdentifiers": {"a": 1}}), encoding="utf-8")
    assert load_approval_entries(path) == []
