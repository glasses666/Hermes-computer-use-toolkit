# Source checkpoint

This public repo was bootstrapped from the Hermes internal computer-use worktree after the contract freeze and the latest verified hardening slices below.

## Internal source branch state at extraction time
- worktree: `~/.hermes/hermes-agent/.worktrees/computer-use-pr-clean`
- latest verified slice at extraction time:
  - `dd7ba1f2` — `[verified] fix: harden keyboard session targeting`

## Recent verified slices already landed before extraction
- `195831cc` — `[verified] fix: reject malformed worker manifest fallback`
- `2dca7f44` — `[verified] fix: harden temporary approval session targeting`
- `b56058f9` — `[verified] fix: harden set_value session targeting`
- `8f1a81bc` — `[verified] fix: ignore malformed worker manifests without action identity`
- `39325fc9` — `[verified] fix: recheck targeted drag session before queueing`
- `1a2f0a4d` — `[verified] fix: harden secondary action session recheck`
- `77150847` — `[verified] fix: recheck queued scroll session targeting`
- `50620ead` — `[verified] fix: harden click session targeting and worker notify`

## Why this matters

This extraction target is not starting from a blank sketch.
It is being opened publicly only after:
- contract freeze
- extraction seam mapping
- a sustained run of verified fail-closed hardening on the internal branch

That gives afternoon multi-agent work a stable public home instead of continuing to bury the line inside the main Hermes repo.
