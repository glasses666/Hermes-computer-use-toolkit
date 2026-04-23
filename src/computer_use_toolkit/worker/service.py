from __future__ import annotations

from typing import Any

from computer_use_toolkit.state.manifests import pending_action_identity



def prioritize_pending_actions(
    pending_actions: list[dict[str, Any]],
    *,
    preferred_app_session_id: str | None = None,
    preferred_action_id: str | None = None,
) -> list[dict[str, Any]]:
    wanted_session_id = str(preferred_app_session_id or "").strip()
    wanted_action_id = str(preferred_action_id or "").strip()
    if not wanted_session_id and not wanted_action_id:
        return list(pending_actions)

    prioritized: list[dict[str, Any]] = []
    remainder: list[dict[str, Any]] = []
    for session in pending_actions:
        session_id = str((session or {}).get("app_session_id") or "").strip()
        identity = pending_action_identity(session) if isinstance(session, dict) else None
        action_id = identity[0] if identity else ""
        matches = True
        if wanted_session_id and session_id != wanted_session_id:
            matches = False
        if wanted_action_id and action_id != wanted_action_id:
            matches = False
        if matches:
            prioritized.append(session)
        else:
            remainder.append(session)
    return prioritized + remainder



def requested_pending_actions(
    pending_actions: list[dict[str, Any]],
    *,
    preferred_app_session_id: str | None = None,
    preferred_action_id: str | None = None,
    manifest_fallback: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    wanted_session_id = str(preferred_app_session_id or "").strip()
    wanted_action_id = str(preferred_action_id or "").strip()
    if not wanted_session_id and not wanted_action_id:
        return list(pending_actions)

    preferred = prioritize_pending_actions(
        pending_actions,
        preferred_app_session_id=wanted_session_id,
        preferred_action_id=wanted_action_id,
    )

    exact_matches: list[dict[str, Any]] = []
    for session in preferred:
        session_id = str((session or {}).get("app_session_id") or "").strip()
        identity = pending_action_identity(session) if isinstance(session, dict) else None
        action_id = identity[0] if identity else ""
        if wanted_session_id and session_id != wanted_session_id:
            continue
        if wanted_action_id and action_id != wanted_action_id:
            continue
        exact_matches.append(session)
    if exact_matches:
        return exact_matches

    if not isinstance(manifest_fallback, dict):
        return []
    manifest_session_id = str(manifest_fallback.get("app_session_id") or "").strip()
    if wanted_session_id and manifest_session_id != wanted_session_id:
        return []
    identity = pending_action_identity(manifest_fallback)
    if identity is None:
        return []
    action_id, _action_type = identity
    if wanted_action_id and action_id != wanted_action_id:
        return []
    return [manifest_fallback]
