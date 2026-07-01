# Work-Order R5: Validate the `tokens_saved` metric

Date: 2026-07-01
From: sessions/coordinator session (Claude, main)
To: delegate-skill orchestrator session `agenthost-delegate-skill-20260630-1934`
Related: `docs/telemetry_improvement_plan_20260630.md` §6.2 R5; the now-merged R1 aggregator.

## Why this exists
In the reconciled plan, the headline savings figures (devin ~88,947 vs kimi ~482 tokens
saved) were computed with the OLD lossy dedup key — whole-second `isoformat()` timestamps
with the token fields excluded from the key — so same-second events could collapse and
`estimated_tokens_saved` could be corrupted. R1 (global aggregator with per-repo
attribution + a per-event `uuid` dedup key) is now merged. R5 is the follow-up: re-measure
`tokens_saved` on the robust key and confirm whether the figures actually hold.

## Task (read-only measurement — no behavior changes)
1. Run the merged global aggregator over all `*/artifacts/<delegate>/events.jsonl{,.1-4}`
   across workspace roots + the `/home/agents` catch-all, using the new uuid-based dedup
   (fall back to `(timestamp,event,task_class,status,latency,estimated_tokens_saved)` for
   pre-uuid historical rows).
2. Recompute per-delegate `tokens_saved` on the deduped set and compare against the plan's
   88.9k / 482 figures. Report the delta.
3. Sanity-check the calculation itself: how is `estimated_tokens_saved` derived per event,
   and is the metadata consistent across delegates (grok added `total_cost_usd` /
   `total_savings_usd` — confirm that doesn't skew the sum)?
4. Report: are the cited figures trustworthy, approximately right, or materially wrong?
   If wrong, give the corrected numbers. Update the plan doc's R5 line and the ledger with
   the finding.

## Guardrails (non-negotiable)
- Read-only / measurement only. No routing or wrapper changes off the back of this.
- Never bypass wrappers; no secrets in telemetry.
- Owned repos, clean trees. Do NOT commit/push without the user's approval.
