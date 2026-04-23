from __future__ import annotations

import uuid
from typing import Any



def build_pending_pointer_action(action_type: str, **fields: Any) -> dict[str, Any]:
    normalized_action_type = str(action_type or "").strip().lower()
    if not normalized_action_type:
        raise ValueError("action_type is required")
    payload = {
        "action_id": f"ptr-{uuid.uuid4().hex}",
        "action_type": normalized_action_type,
    }
    for key, value in fields.items():
        if value is not None:
            payload[key] = value
    return payload



def payload_action_identity(payload: dict[str, Any]) -> tuple[str, str] | None:
    action_id = str(payload.get("action_id") or "").strip()
    action_type = str(payload.get("action_type") or "").strip().lower()
    if not action_id or not action_type:
        return None
    return action_id, action_type
