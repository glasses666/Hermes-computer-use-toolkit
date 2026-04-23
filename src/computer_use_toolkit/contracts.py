from __future__ import annotations

from pathlib import Path

CONTRACT_VERSION = "0.1.0"

PUBLIC_V1_TOOLS = (
    "list_apps",
    "list_active_sessions",
    "list_approved_apps",
    "approve_app",
    "grant_temporary_app_approval",
    "revoke_app",
    "get_app_state",
    "stop_app_session",
    "type_text",
    "press_key",
    "click",
    "scroll",
    "drag",
    "set_value",
    "perform_secondary_action",
)

ADMIN_V1_TOOLS = (
    "detached_worker_status",
    "ensure_detached_worker",
    "stop_detached_worker",
    "set_pointer_execution_mode",
    "list_pending_pointer_actions",
    "claim_pending_pointer_action",
    "report_pointer_action_result",
    "execute_pending_pointer_action_locally",
)


def docs_root() -> Path:
    return Path(__file__).resolve().parents[2] / "docs"


def contract_doc_path() -> Path:
    return docs_root() / "contract-v1.md"


def extraction_seams_doc_path() -> Path:
    return docs_root() / "extraction-seams.md"
