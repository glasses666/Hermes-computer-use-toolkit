# Hermes Computer Use Toolkit

Hermes Computer Use Toolkit is the public extraction target for Hermes' macOS computer-use control plane.

It exists because the original implementation grew inside the main `hermes-agent` repo long enough that the contract needed to be frozen before more feature work fanned out across multiple agents.

## Current scope

This repo currently publishes:
- the frozen v1 contract
- the extraction seam map
- the first standalone Python package scaffold
- pure helper modules for:
  - session manifest paths
  - pending-action identity parsing
  - approval-store normalization / legacy fallback loading
  - queue payload construction
  - queue claim/report state transitions
  - worker-side requested-action selection
- compatibility-oriented tests for those extracted helpers

## What is still in the Hermes repo today

The full production implementation still lives in the Hermes branch while extraction continues:
- MCP tool registration and response glue
- macOS AX/native execution adapters
- detached worker IPC server loop
- live claim/report state machine wiring
- Hermes-specific compatibility smoke tests

This repo is the clean external home the rest of that logic will move into.

## Frozen contract and execution docs

- `docs/contract-v1.md`
- `docs/extraction-seams.md`
- `docs/source-checkpoint.md`
- `docs/migration-execution-plan.md`

These documents are the boundary line for future extraction work and the local execution map for the next small migration slices.

## Package layout

```text
src/computer_use_toolkit/
  contracts.py
  mcp_server.py
  state/
    approval_store.py
    manifests.py
    session_store.py
  queue/
    actions.py
    claims.py
  worker/
    service.py
tests/
  test_contract_smoke.py
  test_queue_actions.py
  test_queue_claims.py
  test_state_approval_store.py
  test_state_manifests.py
  test_worker_service.py
```

## Verification

```bash
python3 -m pytest -q
python3 -m py_compile \
  src/computer_use_toolkit/__init__.py \
  src/computer_use_toolkit/contracts.py \
  src/computer_use_toolkit/mcp_server.py \
  src/computer_use_toolkit/state/__init__.py \
  src/computer_use_toolkit/state/approval_store.py \
  src/computer_use_toolkit/state/manifests.py \
  src/computer_use_toolkit/state/session_store.py \
  src/computer_use_toolkit/queue/__init__.py \
  src/computer_use_toolkit/queue/actions.py \
  src/computer_use_toolkit/queue/claims.py \
  src/computer_use_toolkit/worker/__init__.py \
  src/computer_use_toolkit/worker/service.py \
  tests/test_contract_smoke.py \
  tests/test_queue_actions.py \
  tests/test_queue_claims.py \
  tests/test_state_approval_store.py \
  tests/test_state_manifests.py \
  tests/test_worker_service.py
```

## Immediate next extraction lanes

1. Promote the pure worker backlog-selection seam into toolkit `main` (`worker_pending_backlog` in `src/computer_use_toolkit/worker/service.py`) using the red/green plan in `docs/migration-execution-plan.md`.
2. Keep Hermes integration separate: add the Hermes regression first, then replace only the duplicated worker-selection helper after toolkit tests pass.
3. Extract worker execution and IPC after worker selection is import-stable.
4. Move MCP facade last, once lower layers are stable and Hermes black-box compatibility smokes still pass.

The point of publishing this early is to make the line of work visible and divisible before multi-agent execution starts.
