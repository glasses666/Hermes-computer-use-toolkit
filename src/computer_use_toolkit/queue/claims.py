from __future__ import annotations

"""Pure compatibility helpers for Hermes queue claim/report state transitions.

These helpers intentionally mirror the current Hermes source-checkpoint semantics
while moving queue state-machine logic into the toolkit.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
import uuid



def _parse_iso_datetime(raw_value: Any) -> datetime | None:
    text = str(raw_value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)



def _fresh_virtual_cursor() -> dict[str, Any]:
    return {"x": None, "y": None, "detached": True, "visible": True}



def claim_pending_action(
    session: dict[str, Any],
    *,
    action_id: str,
    worker_id: str,
    now: datetime,
    claim_ttl_seconds: int,
    claim_token_factory: Callable[[], str] | None = None,
) -> dict[str, Any]:
    updated_session = deepcopy(session)
    pending = updated_session.get("pending_pointer_action")
    wanted_action_id = str(action_id or "").strip()
    claimer = str(worker_id or "").strip()

    if not wanted_action_id:
        return {"success": False, "reason": "action_id_required", "session": updated_session}
    if not claimer:
        return {"success": False, "reason": "worker_id_required", "session": updated_session}
    if not isinstance(pending, dict):
        return {"success": False, "reason": "action_required", "session": updated_session}
    if str(pending.get("action_id") or "").strip() != wanted_action_id:
        return {"success": False, "reason": "action_mismatch", "session": updated_session}

    existing_claimer = str(pending.get("claimed_by") or "").strip()
    claim_expires_at = _parse_iso_datetime(pending.get("claim_expires_at"))
    if existing_claimer and (claim_expires_at is None or claim_expires_at > now):
        return {
            "success": False,
            "reason": "action_claimed",
            "claimed_by": existing_claimer,
            "session": updated_session,
        }

    token_factory = claim_token_factory or (lambda: f"claim-{uuid.uuid4().hex}")
    claim_token = token_factory()
    pending["claimed_by"] = claimer
    pending["claimed_at"] = now.isoformat()
    pending["claim_expires_at"] = (now + timedelta(seconds=claim_ttl_seconds)).isoformat()
    updated_session["pending_pointer_claim_token"] = claim_token
    updated_session["last_pointer_action_result"] = None
    return {
        "success": True,
        "reason": "claimed",
        "claim_token": claim_token,
        "session": updated_session,
    }



def report_pending_action_result(
    session: dict[str, Any],
    *,
    action_id: str,
    status: str,
    claim_token: str | None,
    now: datetime,
    x: int | None = None,
    y: int | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    updated_session = deepcopy(session)
    pending = updated_session.get("pending_pointer_action")
    wanted_action_id = str(action_id or "").strip()
    normalized_status = str(status or "").strip().lower()
    provided_claim_token = str(claim_token or "").strip()

    if not wanted_action_id:
        return {"success": False, "reason": "action_id_required", "session": updated_session}
    if normalized_status not in {"completed", "failed"}:
        return {"success": False, "reason": "invalid_status", "session": updated_session}
    if not isinstance(pending, dict):
        return {"success": False, "reason": "action_required", "session": updated_session}
    if str(pending.get("action_id") or "").strip() != wanted_action_id:
        return {"success": False, "reason": "action_mismatch", "session": updated_session}

    existing_claimer = str(pending.get("claimed_by") or "").strip()
    required_claim_token = str(updated_session.get("pending_pointer_claim_token") or "").strip()
    claim_expires_at = _parse_iso_datetime(pending.get("claim_expires_at"))
    if existing_claimer and claim_expires_at is not None and claim_expires_at <= now:
        return {
            "success": False,
            "reason": "claim_expired",
            "claimed_by": existing_claimer,
            "session": updated_session,
        }
    if existing_claimer and (not required_claim_token or provided_claim_token != required_claim_token):
        return {
            "success": False,
            "reason": "action_claimed",
            "claimed_by": existing_claimer,
            "session": updated_session,
        }

    cursor = updated_session.get("virtual_cursor")
    if not isinstance(cursor, dict):
        cursor = _fresh_virtual_cursor()
        updated_session["virtual_cursor"] = cursor
    if x is not None:
        cursor["x"] = x
    if y is not None:
        cursor["y"] = y

    result_payload = {
        **pending,
        "status": normalized_status,
    }
    if existing_claimer:
        result_payload["reported_by"] = existing_claimer
    if x is not None:
        result_payload["x"] = x
    if y is not None:
        result_payload["y"] = y
    if error:
        result_payload["error"] = error

    updated_session["pending_pointer_action"] = None
    updated_session["pending_pointer_claim_token"] = ""
    updated_session["last_pointer_action_result"] = result_payload
    return {
        "success": True,
        "reason": "reported",
        "status": normalized_status,
        "result": result_payload,
        "session": updated_session,
    }
