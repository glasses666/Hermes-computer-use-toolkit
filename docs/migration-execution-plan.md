# Computer-use migration execution plan

Last audited: 2026-04-28

This repo is now past the contract-only phase.  The safe migration direction is to keep extracting small, pure seams into `computer-use-toolkit`, then make Hermes import those seams only after the toolkit tests and Hermes black-box compatibility tests agree.

## Current audited source points

| Source | Worktree / branch | Current head | Role |
|---|---|---:|---|
| Hermes compatibility source | `~/.hermes/hermes-agent/.worktrees/computer-use-pr-clean` / `feat/computer-use-pr-clean` | `60252990` | Frozen v1 contract docs, current in-repo MCP/worker implementation, Hermes-side black-box smokes. |
| Toolkit main | `~/.hermes/computer-use-toolkit` / `main` | `5a2caa7` | Public extraction target with state, approval, queue, and worker-selection helpers already present. |
| Toolkit queue lane | `~/.hermes/computer-use-toolkit/.worktrees/lane-cu-queue` / `lane-cu-queue` | `dd81a1e` | Clean queued-worker helper lane; contains the next smallest pure seam candidate. |
| Toolkit state lane | `~/.hermes/computer-use-toolkit/.worktrees/lane-cu-state` / `lane-cu-state` | `89da518` | Clean approval/session hardening lane; use as reference when touching approval/session parity. |

## Ownership split for the next migration slices

Reference docs for every slice: `docs/contract-v1.md`, `docs/extraction-seams.md`, and `docs/source-checkpoint.md`.

| Layer | Toolkit should own | Hermes should keep until replacement is proven | Required tests before Hermes imports toolkit code |
|---|---|---|---|
| Contract surface | `docs/contract-v1.md`, `src/computer_use_toolkit/contracts.py`, importable placeholder `src/computer_use_toolkit/mcp_server.py` | MCP tool registration and response glue in `computer_use_mcp_server.py` | Toolkit `tests/test_contract_smoke.py`; Hermes `tests/tools/test_computer_use_mcp_contract.py`. |
| State manifests | `src/computer_use_toolkit/state/session_store.py`, `src/computer_use_toolkit/state/manifests.py` | Session manifest writes and live session registry in `computer_use_mcp_server.py` | Toolkit `tests/test_state_manifests.py`; Hermes manifest-backed worker tests. |
| Approval store | `src/computer_use_toolkit/state/approval_store.py` | Hermes approval UX and temporary approval session mutation | Toolkit `tests/test_state_approval_store.py`; Hermes approval round-trip smoke. |
| Queue payloads/results | `src/computer_use_toolkit/queue/actions.py` | Actual pending-action persistence inside Hermes sessions | Toolkit `tests/test_queue_actions.py`; Hermes queued pointer response tests. |
| Queue claim/report state machine | `src/computer_use_toolkit/queue/claims.py` | Live claim/report wrapper functions and MCP admin tool wrappers | Toolkit `tests/test_queue_claims.py`; Hermes worker/admin claim/report tests. |
| Worker selection | `src/computer_use_toolkit/worker/service.py` | `computer_use_detached_worker.py` loop, IPC server, native/AX execution calls | Toolkit `tests/test_worker_service.py`; Hermes `tests/tools/test_computer_use_detached_worker.py` targeted process-queue tests. |
| Worker execution / IPC | future `src/computer_use_toolkit/worker/execution.py` and `worker/ipc.py` | All live pointer/native/AX execution and socket lifecycle | Add toolkit unit tests first; then Hermes black-box worker smokes. Do not use live pointer/control in cron. |

## Next concrete slice

Promote the smallest verified queue-lane seam into toolkit `main` before touching Hermes imports:

1. In `~/.hermes/computer-use-toolkit`, add a focused failing test to `tests/test_worker_service.py` for `worker_pending_backlog(...)`.
   - Expected behavior: valid manifest backlog wins over adapter-listed backlog.
   - Malformed manifest entries without usable action identity are ignored.
   - Adapter fallback is used only when no usable manifest-backed backlog remains.
2. Implement only the pure helper in `src/computer_use_toolkit/worker/service.py` and export it from `src/computer_use_toolkit/worker/__init__.py`.
3. Verify without live pointer/control:
   ```bash
   source /Users/dracoglasser/.hermes/hermes-agent/venv/bin/activate
   pytest -q tests/test_worker_service.py
   pytest -q tests/test_contract_smoke.py tests/test_queue_actions.py tests/test_queue_claims.py tests/test_state_manifests.py tests/test_state_approval_store.py tests/test_worker_service.py
   python3 -m py_compile src/computer_use_toolkit/worker/service.py src/computer_use_toolkit/worker/__init__.py tests/test_worker_service.py
   ```
4. Only after toolkit `main` is green, add the matching Hermes regression/import slice in `~/.hermes/hermes-agent/.worktrees/computer-use-pr-clean`:
   - start with a Hermes failing test in `tests/tools/test_computer_use_detached_worker.py` proving malformed manifest backlog does not block valid adapter fallback;
   - replace only the duplicated selection helper in `computer_use_detached_worker.py` with the toolkit helper;
   - rerun the focused detached-worker tests plus the MCP contract smoke.

## Stop conditions

- Do not restart or kill Hermes gateway, Clash, model servers, or detached long-lived services for these slices.
- Do not call live pointer/control from cron; keep tests pure or patched at native macOS boundaries.
- If a branch already contains the candidate helper, prefer replaying it through the same red/green tests on the target branch instead of broad merges.
- If the same blocker appears three times, search `docs/`, `git log --all --oneline`, and the Hermes worktree tests before attempting another fix.
