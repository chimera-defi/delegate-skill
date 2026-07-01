# Work-Order: Simplify delegates + fold in reconciled telemetry findings

Date: 2026-07-01
From: sessions/coordinator session (Claude, main)
To: delegate-skill orchestrator session `agenthost-delegate-skill-20260630-1934`
Related: `docs/telemetry_improvement_plan_20260630.md` (§6 RECONCILED v2 — read that first)

## Why this exists
The coordinator ran a telemetry review of the three delegates (devin/kimi/grok) plus two
adversarial reviews (advisor red-team + kimi delegate). The user then directed: **keep each
delegate skill simple and small, and move the "extra" tooling into the delegate-skill workspace
folder** (this repo) — NOT a new `~/.agents/...` dir, NOT the individual delegate repos. Core
boundary = **conservative** (verify wiring, break nothing). This work-order hands that to you to
execute as part of your existing WP-A…WP-F pass. The coordinator will NOT edit the delegate repos
itself (scope: session-spawn/coordination only).

## Overlap with your current work-packages (reconcile, don't duplicate)
- **WP-B "Unify kimi telemetry schema"** ⟷ **R1**. Extend it: the real problem is telemetry is
  scattered across N per-repo `artifacts/<d>/events.jsonl` files PLUS a `/home/agents` catch-all
  hit whenever the delegate runs from a non-git CWD (the `record` subprocess re-resolves root via
  `repo_root_from_script()` and has **no `--repo-root` arg**). Fix = a **global aggregator that
  preserves per-repo attribution** (add a `repo` field), NOT pinning one root. Also add the
  missing `--repo-root` passthrough (wrapper→`record`) so future writes stop splitting. Fix the
  **lossy dedup key** (whole-second timestamp + token fields excluded → same-second collapse and
  corrupted `tokens_saved`): add a per-event uuid going forward; historical dedup on
  `(timestamp,event,task_class,status,latency,estimated_tokens_saved)`. Point
  `telemetry_dashboard.py` (cwd fallback) and `ci_gate.py` (parents[1]+workspace, imports
  `summarize`) at the aggregator so all three views agree.
- **WP-C "Standardize fallback on codex/spark"** ⟷ fallback hardening. Aligns. Preserve the
  contract: **`auth_error` → exit 126, no auto-retry** (add a test). Don't regress the
  "never bypass wrappers" enforcement in `detect_bypass.py`.

## New work from the user's directive (the "keep it small" part)
**S1 — Strip each delegate `scripts/` to core; move extras into THIS repo.**
Destination: a subdir of the delegate-skill workspace folder (`/home/agents/workspace/delegate-skill/`),
e.g. `delegate-extras/{kimi,devin,shared}/`. Conservative boundary:

- **KEEP in each delegate repo (core):** `delegate.py`, `<d>_delegate_telemetry.py`, `fallback.py`,
  `detect_bypass.py`, `repo_scan.py`, `plan_prompt.py`, `env_check.py`, the shim + wrapper-binary
  (`pi-shim`/`pi-wrapper-binary`, `devin-shim`/`devin-wrapper-binary`), `setup.sh`, `*-manage.sh`.
- **MOVE to delegate-extras (extra):** `audit_workspace_skills.py`, `audit_workspace_usage.py`,
  `generate_dashboard.py`/`telemetry_dashboard.py`, `install_workspace_skill.py`, `interactive.py`,
  `session_nudge.py`, `tune_timeouts.py`, `ci_gate.py`, and the devin-only advanced modules
  (`mcp_server.py`, `parallel_batch.py`, `cost_estimator.py`, `result_cache.py`,
  `safety_sandbox.py`, `validate_config.py`, `review_devin_delegate.py`,
  `summarize_devin_delegate.py`).
- **Before each move:** grep for imports/exec/`subprocess` references from the core files, setup,
  shims, and git hooks. If something core imports it, either keep it or leave a thin loader that
  adds the extras dir to `sys.path`. `grok-delegate` is already the minimal 7-script template —
  use it as the reference shape; do not bloat it.
- **Verify after:** run `<d>-delegate --check` (env_check) and run the repos' test files with
  `python3` directly (**`pytest` on PATH is a stub that prints "No tests collected"**). Nothing
  should break.

**S2 — Don't build a cross-repo shared Python package.** The kimi review flagged it as a single
point of failure across 3 independent repos at ~72 lifetime calls; coordination cost > duplication
cost. Only `repo_scan.py` (md5-identical ×3) and `plan_prompt.py`/`detect_bypass.py` (differ only
in name strings) are truly identical; `*_telemetry.py` has **diverged** (grok added
`total_cost_usd`/`total_savings_usd`). If you dedupe anything, limit it to the 3 identical files and
gate on regression tests + an observed drift bug.

## Decisions handed down (do not re-litigate)
- **grok = DORMANT, not deprecated.** Revival gate: ≥5 successful calls + a documented devin
  failure on a large repo. (1 lifetime call, auth_error — that's broken auth, not no demand.)
- **No kimi/grok routing policy change on ~72 calls.** Turn R4 into a measured A/B (same small
  summarize/research tasks through devin vs kimi, measured via the R1 aggregator); require ≥20
  successful kimi calls before reshaping.
- **R3 (routing-doc fix) is safe to ship now:** update the CLAUDE.md routing table + SKILL.md so
  devin reads as the general implement/review workhorse (browser/sandbox = a sub-capability), and
  kimi's niche = cheap small read-only.
- **R5:** validate the `tokens_saved` calc before citing it (devin ~88.9k vs kimi ~482 are
  approximate — computed with the lossy key).

## Guardrails (non-negotiable)
- Never bypass wrappers; `auth_error → 126` no retry; no secrets in telemetry.
- Owned repos only, clean trees only — don't clobber dirty work. Don't commit/push without the
  user's approval. Prefer git mv so moves are reversible.
