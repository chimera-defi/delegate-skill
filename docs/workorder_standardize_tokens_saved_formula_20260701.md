# Work-Order: Standardize the `estimated_tokens_saved` derivation across wrappers

Date: 2026-07-01
From: delegate-skill orchestrator session `agenthost-delegate-skill-20260630-1934`
Origin: follow-up to R5 (`docs/workorder_r5_validate_tokens_saved_20260701.md` /
`docs/telemetry_improvement_plan_20260630.md` §6.2 R5 RESOLVED). R5 proved the cited
`tokens_saved` figures were stale (not dedup-corrupted) but surfaced a **real defect**:
the per-event `estimated_tokens_saved` formula is inconsistent across the three wrappers,
so cross-delegate `tokens_saved` comparisons are apples-to-oranges.

## Why this exists
`estimated_tokens_saved` is meant to estimate the parent-context tokens the orchestrating
Claude avoided by delegating. Today each wrapper computes it differently — along **two**
axes, not one:

| wrapper | file:line | `parent_tokens` source | formula |
|---------|-----------|------------------------|---------|
| devin | `scripts/delegate.py:1335,1352` | `envelope.metrics.parent_context_tokens` (measured) | `max(0, max(parent_tokens, delegate_input_tokens) * 3 - delegate_output_tokens)` |
| kimi | `scripts/delegate.py:822,825` | `envelope.metrics.parent_context_tokens` (measured) | `max(0, parent_tokens - delegate_output_tokens)` — **no ×3, no `max()` inner term** |
| grok | `scripts/delegate.py:599,602` | `estimate_tokens(json.dumps(envelope))` (envelope-size **estimate**, NOT the measured metric) | `max(0, parent_tokens * 3 - delegate_output_tokens)` |

Consequences:
- **kimi structurally under-counts** vs devin/grok (missing the ×3 heuristic), which is why
  its headline number looked tiny (482 in the plan snapshot; 55,326 now) next to devin.
- **grok measures a different quantity** (envelope byte-size × token estimate) than
  devin/kimi (the real parent context window), so even with the same ×3 it is not comparable.

## Task (behavior change — wrapper edits; requires approval before merge)
1. **Agree the canonical definition** (this is a judgment call — surface it to the user before
   implementing, do not silently pick):
   - **`parent_tokens` source:** standardize on `envelope.metrics.parent_context_tokens`
     (already used by devin + kimi; the measured parent context is the right notion of "what
     the parent would have spent"). grok must switch to reading it, with a documented fallback
     to `estimate_tokens(json.dumps(envelope))` only when the metric is absent/zero.
   - **Multiplier `K`:** devin and grok use `K=3`; kimi uses `K=1`. Recommend `K=3` (majority +
     the heuristic that a parent re-reading/reasoning over context spends ~3× the raw tokens),
     but this changes kimi's metric meaning — get explicit ratification.
   - **Inner `max(parent_tokens, delegate_input_tokens)` term:** devin has it, the others don't.
     Recommend dropping it for simplicity (parent_context_tokens already dominates
     delegate_input_tokens in practice) OR adopting it everywhere — pick one, apply uniformly.
2. **Canonical formula (fill in K + inner-term decision), applied byte-identically in all three:**
   ```
   parent_tokens = envelope.metrics.parent_context_tokens  (fallback: envelope-size estimate)
   estimated_tokens_saved = max(0, parent_tokens * K - delegate_output_tokens)
   ```
   Extract it into ONE shared helper if practical (e.g. a function in
   `delegate-extras/shared/`) so the three wrappers cannot drift again; otherwise leave an
   identical inline block in each with a comment pointing at this work-order.
3. **Keep the USD path consistent** but note the R1 aggregator
   (`delegate-extras/shared/aggregate_telemetry.py`) is the source of truth for USD — it
   recomputes savings centrally from `pricing.json` off the token field. Per-wrapper
   `estimated_savings_usd` (grok L607) is secondary; just keep it derived from the same
   `estimated_tokens_saved` so it doesn't contradict the aggregator.
4. **Document the discontinuity.** Changing the formula does NOT (and must not) rewrite
   historical events — telemetry is append-only/read-only. So each delegate's `tokens_saved`
   series will have a step at the cutover. Add a one-line note to the plan doc R5 section and
   to `delegate-extras/README.md` so future readers don't misread the jump as a regression.

## Verification
- `devin/kimi/grok --check` all green after edits (formula change must not affect `--check`).
- A real `--task` run per delegate emits an event whose `estimated_tokens_saved` matches the
  new formula by hand-calc (log `parent_tokens`, `delegate_output_tokens`, K).
- Re-run the R5 measurement scripts (`/tmp/r5_measure.py`) — new events should show the three
  formulas now agree in structure; the raw `parent_context_tokens` still differs per run (fine).
- Per-repo tests pass via `python3 -c "import pytest,sys; sys.exit(pytest.main(['<dir>','-q']))"`
  (the `pytest` CLI is a local stub); index `tests/smoke.sh` + `delegate-extras/shared/tests` green.

## Guardrails (non-negotiable)
- **Never bypass wrappers** (`opencode` / `pi --provider …` / `devin` raw). No secrets in telemetry.
- **Owned repos, clean trees.** Do NOT commit/push without the user's approval. Prefer minimal,
  reviewable diffs. One PR per delegate repo (+ optionally one to the index repo for a shared helper).
- **Read-only on history:** never mutate existing `events.jsonl` rows; the change is forward-only.
- SDD: one Sonnet builder + one Opus reviewer per repo, orchestrator verifies the diff before merge.
- Commit format: `type(scope): subject [Agent: Claude Sonnet 4.6]` (+ `[Agent: Claude Opus 4.8]`
  for orchestrator commits), `Co-authored-by: Chimera <chimera_defi@protonmail.com>`,
  `Co-Authored-By: Claude <noreply@anthropic.com>`.
