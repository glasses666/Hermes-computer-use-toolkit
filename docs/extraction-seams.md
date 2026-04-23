# Computer-use extraction seams

This document maps the current in-repo implementation to the layers that should become the external computer-use toolkit.

The intent is to extract by seam, not by wholesale rewrite.

## Current implementation hotspots

### 1. MCP/tool facade

Current home:
- `computer_use_mcp_server.py`
- `register_tools(mcp)` wrapper section near the bottom of the file

Current responsibilities:
- expose MCP tools
- validate arguments just enough to route to implementation helpers
- shape outward response envelopes

Extraction seam:
- future toolkit `mcp_server.py` or `server/mcp.py`
- Hermes should eventually keep only thin consumer glue or external MCP configuration

Keep stable:
- tool names
- argument schemas
- response envelope semantics documented in `docs/computer-use-contract-v1.md`

### 2. Session + approval state

Current home in `computer_use_mcp_server.py`:
- `_APP_SESSIONS`, `_APPROVALS_LOCK`, `_APP_SESSIONS_LOCK`
- `_approval_store_path()`, `_load_approvals()`, `_save_approvals()`
- `_ensure_app_session()`, `_find_session()`, `_resolve_session()`
- `_session_payload()`, `_write_session_state()`, `_sync_session_artifacts()`

Current responsibilities:
- in-memory session registry
- approval persistence and temporary approval bookkeeping
- session manifest persistence under `~/.hermes/computer-use/session-state/`
- shaping session payloads returned to callers and workers

Extraction seam:
- future toolkit `state/session_store.py`
- future toolkit `state/approval_store.py`
- explicit manifest schema module for queued actions and session snapshots

Important boundary:
- manifest-backed state is already a cross-process compatibility layer; keep it stable while Hermes migrates.

### 3. Local macOS execution adapter

Current home in `computer_use_mcp_server.py`:
- `computer_control(...)` calls
- `detached_ax_perform_action(...)`
- `detached_ax_set_value(...)`
- `_execute_secondary_action_at_point(...)`
- helpers for cursor overlays and coordinate normalization

Current responsibilities:
- translate semantic actions into native macOS operations
- perform AX-first behavior where supported
- fall back to native click/type/paste only when explicitly allowed by current semantics

Extraction seam:
- future toolkit `adapters/macos_native.py`
- future toolkit `adapters/macos_ax.py`
- optional `artifacts/overlay.py` for preview image generation

Keep stable:
- fail-closed semantics for unsupported/incomplete actions
- no hidden broadening of fallback behavior during extraction

### 4. Queue lifecycle / helper bridge

Current home in `computer_use_mcp_server.py`:
- `_record_pending_pointer_action()`
- `list_pending_pointer_actions_impl()`
- `claim_pending_pointer_action_impl()`
- `report_pointer_action_result_impl()`
- `execute_pending_pointer_action_locally_impl()`
- `_queue_pointer_action_response()`
- `set_pointer_execution_mode_impl()`

Current responsibilities:
- create queued action manifests
- helper claim/report state machine
- local fallback execution path for legacy/incomplete queued actions
- notify detached worker with targeted `(app_session_id, action_id)` payloads

Extraction seam:
- future toolkit `queue/actions.py`
- future toolkit `queue/claims.py`
- future toolkit `queue/notifications.py`

Keep stable:
- `(app_session_id, action_id)` target specificity
- fail-closed claim/report semantics
- manifest-first precedence when manifest backlog exists

### 5. Detached worker service

Current home:
- `computer_use_detached_worker.py`

Current responsibilities:
- IPC server loop
- manifest discovery and hydration
- worker-owned execution for queued `click`, `scroll`, `drag`, `set_value`, `secondary_action`
- serialization of `run_once`, `process_queue`, and `execute_action` under one execution lock

Key functions:
- `_pending_actions_from_session_state()`
- `_requested_pending_actions()`
- `_execute_pending_action_via_service()`
- `run_worker_once(...)`
- `handle_ipc_request(...)`
- `_ipc_server_loop(...)`

Extraction seam:
- future toolkit `worker/service.py`
- future toolkit `worker/ipc.py`
- future toolkit `worker/execution.py`

Keep stable:
- manifest-first backlog behavior
- targeted hydration for `execute_action` / `process_queue`
- no side door around the worker lock

### 6. Tests that should become compatibility tests

Current homes:
- `tests/tools/test_computer_use_mcp_server.py`
- `tests/tools/test_computer_use_detached_worker.py`

Recommended split after extraction:
- toolkit-owned behavior/unit tests for queue, worker, adapter, and manifest semantics
- Hermes-owned black-box compatibility smoke tests that prove Hermes can still call the external toolkit contract correctly

## Proposed external toolkit layout

A minimal first extraction could look like:

```text
computer-use-toolkit/
  pyproject.toml
  README.md
  docs/
    contract-v1.md
    extraction-seams.md
  src/computer_use_toolkit/
    contracts.py
    mcp_server.py
    state/
      approval_store.py
      session_store.py
      manifests.py
    adapters/
      macos_native.py
      macos_ax.py
      overlays.py
    queue/
      actions.py
      claims.py
      notifications.py
    worker/
      execution.py
      ipc.py
      service.py
  tests/
    test_contract_smoke.py
    test_worker_service.py
    test_queue_claims.py
    test_macos_adapter.py
```

## Hermes-side code after extraction

Hermes should retain only thin consumer glue:
- MCP server registration or config pointing at the toolkit package/server
- approval UX integration specific to Hermes surfaces if it cannot live in the toolkit
- black-box smoke tests proving Hermes still speaks the frozen v1 contract

Hermes should stop owning the majority of:
- manifest schema rules
- claim/report state machine
- worker IPC semantics
- service-owned queued action execution internals

## Safe extraction order

1. Freeze the contract doc.
2. Move manifest/session/claim logic into toolkit modules without changing behavior.
3. Move detached worker execution and IPC into toolkit modules.
4. Move MCP facade last, once lower layers are import-stable.
5. Leave Hermes with compatibility tests and configuration glue.

## Red lines during extraction

- Do not change public tool names while moving files.
- Do not let worker execution fall back from manifest-first to stale adapter listings.
- Do not widen click/secondary-action fallback rules accidentally while splitting modules.
- Do not make Hermes depend on toolkit-private internals once the seam is established.
