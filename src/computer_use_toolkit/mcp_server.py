from __future__ import annotations

from .contracts import ADMIN_V1_TOOLS, CONTRACT_VERSION, PUBLIC_V1_TOOLS


def get_contract_summary() -> dict[str, object]:
    return {
        "contract_version": CONTRACT_VERSION,
        "public_v1_tools": list(PUBLIC_V1_TOOLS),
        "admin_v1_tools": list(ADMIN_V1_TOOLS),
    }
