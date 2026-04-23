from __future__ import annotations

import re
from pathlib import Path

_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class InvalidSessionID(ValueError):
    pass



def validate_session_id(app_session_id: str) -> str:
    value = str(app_session_id or "").strip()
    if not value:
        raise InvalidSessionID("app_session_id is required")
    if not _SESSION_ID_RE.fullmatch(value):
        raise InvalidSessionID(f"invalid app_session_id: {app_session_id!r}")
    if value in {".", ".."}:
        raise InvalidSessionID(f"invalid app_session_id: {app_session_id!r}")
    return value



def session_state_root(hermes_home: str | Path) -> Path:
    return Path(hermes_home).expanduser().resolve() / "computer-use" / "session-state"



def session_manifest_path(root: str | Path, app_session_id: str) -> Path:
    normalized_root = Path(root).expanduser().resolve()
    validated = validate_session_id(app_session_id)
    return normalized_root / f"{validated}.json"
