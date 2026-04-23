from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

_APPROVALS_LOCK = Lock()



def approval_store_path(hermes_home: str | Path) -> Path:
    return Path(hermes_home).expanduser().resolve() / "computer-use" / "ComputerUseAppApprovals.json"



def _normalize_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""



def normalize_approval_entry(raw_entry: Any) -> dict[str, str] | None:
    if isinstance(raw_entry, str):
        name = _normalize_text(raw_entry)
        return {"approval_name": name, "bundle_id": "", "bundle_path": ""} if name else None
    if not isinstance(raw_entry, dict):
        return None
    name = _normalize_text(raw_entry.get("approval_name") or raw_entry.get("app_name") or raw_entry.get("label"))
    bundle_id = _normalize_text(raw_entry.get("bundle_id"))
    bundle_path = _normalize_text(raw_entry.get("bundle_path"))
    if not any([name, bundle_id, bundle_path]):
        return None
    if not name:
        name = bundle_id or bundle_path
    return {"approval_name": name, "bundle_id": bundle_id, "bundle_path": bundle_path}



def approval_entry_label(entry: dict[str, str]) -> str:
    return _normalize_text(entry.get("approval_name")) or _normalize_text(entry.get("bundle_id")) or _normalize_text(entry.get("bundle_path"))



def _approval_identity_key(entry: dict[str, str]) -> tuple[str, str, str]:
    return (
        approval_entry_label(entry).casefold(),
        _normalize_text(entry.get("bundle_id")).casefold(),
        _normalize_text(entry.get("bundle_path")).casefold(),
    )



def _approval_sort_key(entry: dict[str, str]) -> tuple[str, str, str]:
    return _approval_identity_key(entry)



def load_approval_entries(path: str | Path) -> list[dict[str, str]]:
    with _APPROVALS_LOCK:
        file_path = Path(path)
        if not file_path.exists():
            return []
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(payload, dict):
            raw_entries = payload.get("approved_app_entries")
            if not isinstance(raw_entries, list):
                approved_apps = payload.get("approved_apps")
                legacy_bundle_ids = payload.get("approvedBundleIdentifiers")
                if isinstance(approved_apps, list) and approved_apps:
                    raw_entries = approved_apps
                elif isinstance(legacy_bundle_ids, list):
                    raw_entries = legacy_bundle_ids
                elif isinstance(approved_apps, list):
                    raw_entries = approved_apps
                else:
                    raw_entries = []
        elif isinstance(payload, list):
            raw_entries = payload
        else:
            raw_entries = []
        entries: list[dict[str, str]] = []
        seen: set[tuple[str, str, str]] = set()
        for raw_entry in raw_entries:
            normalized = normalize_approval_entry(raw_entry)
            if not normalized:
                continue
            key = _approval_identity_key(normalized)
            if key in seen:
                continue
            seen.add(key)
            entries.append(normalized)
        entries.sort(key=_approval_sort_key)
        return entries



def save_approval_entries(path: str | Path, entries: list[dict[str, str]]) -> None:
    with _APPROVALS_LOCK:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        cleaned: list[dict[str, str]] = []
        seen: set[tuple[str, str, str]] = set()
        for raw_entry in entries:
            normalized = normalize_approval_entry(raw_entry)
            if not normalized:
                continue
            key = _approval_identity_key(normalized)
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(normalized)
        cleaned.sort(key=_approval_sort_key)
        payload = {
            "approved_apps": [approval_entry_label(entry) for entry in cleaned],
            "approved_app_entries": cleaned,
        }
        file_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
