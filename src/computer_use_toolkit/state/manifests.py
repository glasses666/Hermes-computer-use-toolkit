from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .session_store import session_manifest_path, validate_session_id



def _manifest_resolves_within_root(path: str | Path, root: str | Path) -> Path | None:
    candidate = Path(path)
    root_path = Path(root).expanduser().resolve()
    try:
        resolved = candidate.resolve(strict=True)
    except Exception:
        return None
    if resolved.parent != root_path or resolved.suffix != ".json":
        return None
    return resolved



def pending_action_identity(payload: dict[str, Any]) -> tuple[str, str] | None:
    pending = payload.get("pending_pointer_action")
    if not isinstance(pending, dict):
        return None
    action_id = str(pending.get("action_id") or "").strip()
    action_type = str(pending.get("action_type") or "").strip().lower()
    if not action_id or not action_type:
        return None
    return action_id, action_type



def load_manifest(path: str | Path) -> dict[str, Any] | None:
    candidate = Path(path)
    if not candidate.exists() or candidate.suffix != ".json":
        return None
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None



def list_pending_session_manifests(root: str | Path) -> list[dict[str, Any]]:
    root_path = Path(root).expanduser().resolve()
    if not root_path.exists():
        return []
    discovered: list[dict[str, Any]] = []
    for path in sorted(root_path.glob("*.json")):
        resolved_path = _manifest_resolves_within_root(path, root_path)
        if resolved_path is None:
            continue
        payload = load_manifest(resolved_path)
        if not payload:
            continue
        app_session_id = str(payload.get("app_session_id") or "").strip()
        try:
            validated = validate_session_id(app_session_id)
        except Exception:
            continue
        if path.stem != validated:
            continue
        if pending_action_identity(payload) is None:
            continue
        discovered.append(payload)
    return discovered



def find_pending_session_manifest(root: str | Path, app_session_id: str, action_id: str | None = None) -> dict[str, Any] | None:
    path = session_manifest_path(root, app_session_id)
    payload = load_manifest(path)
    if not payload:
        return None
    payload_session_id = str(payload.get("app_session_id") or "").strip()
    if payload_session_id != validate_session_id(app_session_id):
        return None
    identity = pending_action_identity(payload)
    if identity is None:
        return None
    found_action_id, _found_action_type = identity
    wanted_action_id = str(action_id or "").strip()
    if wanted_action_id and found_action_id != wanted_action_id:
        return None
    return payload
