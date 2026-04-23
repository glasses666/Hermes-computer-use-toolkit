# Computer-use v1 contract freeze

This document freezes the current macOS computer-use surface into three buckets:

1. **Public v1** — user-facing tools and response behavior we should preserve during extraction.
2. **Admin/internal v1** — control-plane and helper tools that may move into a toolkit package but should keep working while Hermes migrates.
3. **Deferred** — intentionally out of scope for the first frozen contract.

The goal is to stop growing an ambiguous branch-local mini-product and instead lock the behavior that downstream callers can safely depend on.

## Scope

Grounding for this freeze:
- `computer_use_mcp_server.py`
- `computer_use_detached_worker.py`
- recent verified slices through queued `set_value`, `secondary_action`, `click`, `scroll`, `drag`
- session-manifest backed worker execution and claim/report semantics

This is **not** a promise of a true second cursor plane. The current detached worker is still a service-owned execution path over the same local macOS control primitives.

## Public v1

These are the tools and semantics we should preserve for normal callers.

### Discovery and approval

- `list_apps(limit=100)`
- `list_active_sessions()`
- `list_approved_apps()`
- `approve_app(app_name)`
- `grant_temporary_app_approval(app_name, app_session_id=None, scope="once")`
- `revoke_app(app_name)`
- `get_app_state(app_name=None, app_session_id=None)`
- `stop_app_session(app_name=None, app_session_id=None)`

### Direct interaction

- `type_text(text, app_session_id=None)`
- `press_key(key, modifiers=None, app_session_id=None)`
- `click(index=None, x=None, y=None, button="left", click_count=1, app_session_id=None)`
- `scroll(index=None, x=None, y=None, delta_y=0, app_session_id=None)`
- `drag(start_x, start_y, end_x, end_y, app_session_id=None)`
- `set_value(index, value, app_session_id=None)`
- `perform_secondary_action(index, action_name, app_session_id=None)`

### Public v1 behavior guarantees

#### Session targeting

- If `app_session_id` is provided, the action must target that exact session or fail closed with a session-required style error.
- If `app_session_id` is omitted and multiple active sessions exist, the tool should fail closed with `multiple_active_sessions=true` instead of guessing.
- `get_app_state(..., app_session_id=...)` remains the canonical re-entry point for reacquiring a session snapshot.

#### Approval semantics

- Unapproved sessions fail closed.
- Approval may be durable (`approve_app`) or temporary (`grant_temporary_app_approval`).
- Approval-gated responses may clear stale accessibility state rather than returning privileged data for an unapproved session.

#### Element targeting

- `click(index=...)`, `scroll(index=...)`, `set_value(index=...)`, and `perform_secondary_action(index=...)` resolve accessibility-node centers from the approved session tree.
- Missing nodes or unusable frames fail with explicit errors; callers should not have to precompute coordinates for element-targeted actions.

#### Pointer execution modes

- Pointer-like actions may execute immediately or queue through `set_pointer_execution_mode` / detached-worker plumbing.
- Queued execution is still part of the public v1 story because public tools can transparently return queued responses.
- When queued, actions persist manifest-backed state and return enough session payload for the caller to inspect pending status.

#### Result envelope expectations

Public responses should keep these fields stable where applicable:
- `success`
- `session_id`
- session identity fields such as `app_name`, `app_session_id`
- `virtual_cursor`
- `pending_pointer_action`
- `last_pointer_action_result`
- error flags such as `session_required`, `approval_required`, `multiple_active_sessions`

We do **not** need byte-for-byte identical payload ordering, but the semantic fields above should remain compatible.

## Admin/internal v1

These are real interfaces today, but they are control-plane surfaces rather than end-user actions.

### Detached worker lifecycle

- `detached_worker_status()`
- `ensure_detached_worker(worker_id="detached-worker")`
- `stop_detached_worker()`
- `set_pointer_execution_mode(mode, app_session_id=None)`
- `list_pending_pointer_actions()`

### Helper/worker bridge

- `claim_pending_pointer_action(app_session_id, action_id, worker_id)`
- `report_pointer_action_result(app_session_id, action_id, status, claim_token=None, x=None, y=None, error=None)`
- `execute_pending_pointer_action_locally(app_session_id, action_id, worker_id)`

### Admin/internal v1 guarantees

- Queued actions are identified by `(app_session_id, action_id)`.
- Claim/report is fail-closed; stale, missing, expired, or already-claimed actions must not silently execute another action.
- Persisted session manifests are authoritative backlog for worker execution and IPC snapshots when present.
- `execute_action`/`process_queue` worker dispatch must preserve target specificity and not degrade into “run whatever is pending first”.

These tools may move behind a toolkit-internal namespace later, but they should remain behavior-compatible until Hermes-side migration is complete.

## Deferred from v1

These items are intentionally **not** frozen as part of the first externalizable contract:

- a true independent second cursor plane
- generalized permission-dialog handling and over-the-lock-screen UX promises
- non-macOS backends
- broad AX action expansion beyond the currently supported small whitelist
- polished overlay/media UX beyond compatibility with existing preview/state fields
- richer queue scheduling policies than targeted single-action claim/report execution
- repackaging decisions such as final Python package names, CLI names, or repo layout

## Freeze rules for extraction

1. Do not rename public v1 tools during extraction.
2. Do not remove `app_session_id` targeting from supported actions.
3. Do not change queued action ownership semantics so that worker dispatch can execute unrelated pending actions.
4. Treat persisted session-manifest shape and claim/report flow as compatibility boundaries until Hermes-side smoke tests are updated in lockstep.
5. New capabilities should land as additive fields/tools, not silent semantic changes to the frozen v1 set.

## Exit criterion for moving out of the hermes-agent branch

We can treat the contract as frozen enough to extract when:
- the public/admin tool split above is accepted as the compatibility boundary,
- Hermes can consume the toolkit through thin glue instead of owning most service logic inline,
- remaining work is mostly packaging, black-box smoke coverage, and compatibility hardening rather than net-new control-plane semantics.
