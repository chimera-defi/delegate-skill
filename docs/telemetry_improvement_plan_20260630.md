# Delegate-Skill Telemetry-Driven Improvement Plan

Date: 2026-06-30
Author: Claude (main session)
Status: RECONCILED v2 — both reviews complete (advisor verdict: rethink; kimi verdict: overconfident). See section 6.
Implementation owner: `agenthost-delegate-skill-20260630-1934` session (workdir `/home/agents/workspace/delegate-skill`)

## 1. What the telemetry actually says

Aggregated across BOTH telemetry roots (`/home/agents/artifacts/<d>/` and each repo's own
`artifacts/<d>/`), deduped by (timestamp, event, task_class, status, latency):

| Delegate | Invocations | Status | Task classes | Fallback | Tokens saved | Latency med/max |
|----------|------------|--------|--------------|----------|--------------|-----------------|
| **devin** | 49 | 47 ok / 2 err (96%) | implement 27, review 18, debug 3, browser 1 | 3/49 (schema_invalid 2, clarification 1) | **88,947** | 40s / 577s |
| **kimi** | 22 | 15 ok / 4 err / 3 auth (68%) | review 11, summarize 9, search 1, impl-lite 1 | **7/22 (32%)** timeout 4, auth 3 | 482 | 123s / 541s |
| **grok** | 1 | 1 auth_error (0%) | implement 1 | 1/1 auth | 0 (phantom) | — |

### Findings (evidence-backed, not assumptions)
- **F1 — Telemetry is fragmented across two roots.** `repo_root_from_script()` falls back to
  `__file__.parents[3]` (= `/home/agents`) when `git rev-parse` fails, but resolves to the repo
  root when invoked inside a git tree. So the same delegate writes to two different
  `events.jsonl` files depending on the caller's CWD/git context. **No single `summary` call is
  ever complete.** (kimi: 15 events in `/home/agents/artifacts`, 7 in the repo file = 22 real.)
- **F2 — devin is the de-facto general workhorse, not a browser tool.** 45/49 calls (92%) are
  implement+review; browser is 1. The CLAUDE.md routing table markets devin as
  "browser/UI/screenshot/sandbox." Doc and reality have diverged.
- **F3 — devin is healthy and high-value.** 96% success, 88.9k tokens saved, median 40s. It earns
  its keep. The earlier "tokens_saved looks broken (~186)" read was a stale kimi-only number.
- **F4 — kimi is the weak link.** 32% fallback (timeouts dominate now, 3 historical auth errors),
  68% success, only 482 tokens saved over 22 calls. Its main job is review (11) — which overlaps
  devin's review (18) at far higher success.
- **F5 — grok is effectively dead.** One lifetime invocation, auth_error, zero successes, yet it
  carries a full duplicate script set to maintain.
- **F6 — Heavy code duplication across the three repos** (confirmed in prior analysis):
  `repo_scan.py` byte-identical (49 lines ×3); `plan_prompt.py`, `install_workspace_skill.py`
  (~95% identical, differ only in delegate-name strings); `env_check`, `detect_bypass`,
  `install_git_hooks`, `fallback`, `session_nudge`, `tune_timeouts`, `audit_workspace_usage`,
  `ci_gate` all near-identical and drifting.

## 2. Proposed work (ranked by value/effort, evidence-tied)

### P1 — Fix telemetry root fragmentation (F1). HIGH value, LOW effort.
Make `repo_root_from_script()` resolve to ONE stable root per delegate regardless of caller CWD
(e.g. always the delegate's own repo root via `__file__`, dropping the git-rev-parse branch; OR a
fixed `~/.agents/telemetry/<delegate>/`). Migrate/merge the two existing files once. Without this,
every other metric below is measured on partial data.

### P2 — Extract a shared `delegate_common/` library (F6). HIGH value, MED effort.
Pull byte-identical / near-identical modules into one importable package consumed by all three
wrappers: `repo_scan`, `telemetry` (record/load/summarize), `fallback`, `env_check`,
`detect_bypass`, `plan_prompt` (with per-delegate task-class regex passed in), `install_*`,
`ci_gate`. Kills drift; one fix lands everywhere. Sequence AFTER P1 so telemetry is unified first.

### P3 — Reconcile routing docs with reality (F2). MED value, LOW effort.
Update the CLAUDE.md routing table + SKILL.md: devin = general heavy implement/review workhorse
(keep browser/sandbox as a sub-capability); clarify kimi's niche (cheap, small, read-only
summarize) and the explicit "prefer devin for review" guidance given kimi's failure rate.

### P4 — Decide kimi's scope (F4). MED value, LOW effort (decision) + MED (tuning).
Options: (a) keep kimi but restrict to small summarize/search only, route review→devin;
(b) raise kimi timeouts via `tune_timeouts.py` and re-measure; (c) keep as-is. Recommend (a)+(b):
shrink the job to where it succeeds, tune timeouts, re-measure after P1.

### P5 — Decide grok's fate (F5). MED value, LOW effort.
Options: (a) deprecate/remove grok-delegate (it has never succeeded); (b) fix auth + keep as cold
standby for genuinely large-codebase tasks devin can't hold. Recommend (a) unless there is a
concrete large-repo use case devin has failed on — in which case fix auth and add a smoke test.

### P6 — Audit then prune devin-only modules. LOW value, MED effort, HIGH risk.
devin carries unique modules (mcp_server, parallel_batch, result_cache, cost_estimator,
safety_sandbox, telemetry_dashboard, validate_config). DO NOT delete blindly — first grep for
import/exec wiring; keep what's reachable, remove only provably-dead code. Lowest priority.

## 3. Sequencing
P1 → P2 → (P3, P4, P5 in parallel, all doc/decision-light) → P6 last (riskiest).
P1 is the gate: do not re-measure P4/P5 outcomes until telemetry is unified.

## 4. Explicit non-goals / guardrails
- No behavioral change to the "never bypass wrappers" / "auth_error → exit 126, no auto-retry" contracts.
- No secrets touched; no plaintext keys in telemetry.
- Implementation happens in the delegate-skill session, not the coordinator session.

## 5. Open questions for reviewers
- Is unifying to a single telemetry root safe given downstream dashboards (devin has telemetry_dashboard.py)?
- Is the duplication better solved by a shared package vs. a generated-from-template approach?
- Is grok worth keeping purely as insurance for large-context tasks?

---

## 6. RECONCILED v2 (post adversarial review)

Two independent adversarial reviews were run on §1–5: an advisor red-team subagent
(code-verified, verdict **rethink**) and the kimi delegate via its wrapper (verdict
**overconfident given the data**). They converged on most points and disagreed on one
mechanism, which I then settled by reading the wrapper's record path directly.

### 6.1 Settled facts (verified in code, supersede §1 framing where noted)
- **Telemetry is scattered across N repos + a `/home/agents` catch-all** — not "two roots."
  Each delegate's `kimi/grok/devin_delegate_telemetry.py record` subprocess is invoked
  WITHOUT a `--repo-root` arg (no such flag in the `record` subparser), so it re-resolves
  the root itself: `git rev-parse` in its CWD, else `__file__.parents[3]` = `/home/agents`.
  → per-repo files when run inside a git tree; the `/home/agents` file when CWD isn't git.
  Both happen in normal use. (kimi's "wrapper always passes --repo-root" is FALSE; the
  advisor's "fallback is reachable" is correct; kimi's "50+ files / N+1" is also correct.)
- **Three different root resolvers across consumers** (advisor, verified): telemetry scripts
  use `parents[3]`; `telemetry_dashboard.py` falls back to `cwd`; `ci_gate.py` uses
  `parents[1]` + a separate workspace path and imports `summarize` directly. No view agrees.
- **The dedup key is lossy** (advisor): whole-second `isoformat()` timestamps + token fields
  excluded from the key → same-second calls collapse and `tokens_saved` can be corrupted.
  Caveat: my own §1 aggregation used this weak key, so the 88.9k/482 figures are approximate.
- **grok's telemetry has DIVERGED** (advisor, verified): `grok_delegate_telemetry.py` added
  `total_cost_usd`/`total_savings_usd` and filter params. So `*_telemetry.py` is NOT a safe
  shared-lib candidate. Only `repo_scan.py` (md5-identical ×3) and `plan_prompt.py` /
  `detect_bypass.py` (differ only in delegate-name strings) are truly identical.
- **Sample sizes are too small to set policy** (both): ~72 total calls (devin 49, kimi 22,
  grok 1). Any deprecation / routing change must be gated on more data.

### 6.2 Revised work items (these REPLACE §2's P1–P6)
- **R1 — Build a global aggregator; do NOT pin a single root.** Scan all
  `*/artifacts/<delegate>/events.jsonl{,.1-4}` across workspace roots + the `/home/agents`
  fallback; preserve a `repo` attribution field per record. **Fix the dedup key**: start
  writing a per-event `uuid` now; for historical data dedup on
  `(timestamp,event,task_class,status,latency,estimated_tokens_saved)`. Point
  `telemetry_dashboard.py` and `ci_gate.py` at the aggregator so all views agree. Add the
  missing `--repo-root` passthrough (wrapper→`record`) so future writes stop splitting.
  HIGH value, MED effort (bigger than original P1).
- **R2 — De-scope the shared lib; gate on tests.** Extract ONLY `repo_scan.py` (and maybe
  `plan_prompt.py`/`detect_bypass.py`). Do NOT touch `*_telemetry.py`. Prerequisite:
  per-wrapper regression tests + a concrete observed drift bug. Per kimi, a cross-repo
  package is a single point of failure across 3 independent repos — at 72 calls the
  coordination cost may exceed the duplication cost, so **DEFER unless tests exist and a
  drift bug is observed.**
- **R3 — Ship the routing-doc fix NOW.** Pure text, zero data risk, both reviewers agree
  devin is the de-facto implement/review workhorse. Do this first.
- **R4 — Make kimi/grok a measured experiment, not a policy change.** Mark grok **dormant**
  (not deprecated); revival gate = ≥5 successful calls + a documented devin failure on a
  large repo. For kimi, run a controlled A/B (identical small summarize/research tasks
  through devin vs kimi), measured via R1's aggregator; require ≥20 successful kimi calls
  before reshaping routing.
- **R5 — Validate the `tokens_saved` metric before citing it.** Check the calculation +
  metadata consistency (devin 88.9k vs kimi 482) once R1's robust dedup exists.
  - **RESOLVED 2026-07-01 (read-only measurement, merged R1 aggregator).** The cited
    88.9k / 482 figures are a **stale snapshot, NOT dedup-corrupted.** Re-running the OLD
    lossy key (whole-second timestamp, token fields excluded) and the NEW uuid/robust key
    over identical current data yields **identical** `tokens_saved` for all three delegates
    (collapsed=0, saved_lost=0) — the old key never actually merged distinct events or lost
    tokens on this data. The gap is pure temporal accumulation since the plan snapshot.
    **Corrected current figures (deduped, robust key): devin 213,548 (134 calls) /
    kimi 55,326 (137 calls) / grok 408 (1 call).** dup_dropped=0 for all (dataset is
    almost entirely pre-uuid composite rows; no collisions). Metadata audit: no USD-skew —
    `total_cost_usd` / `total_savings_usd` are ABSENT from every invocation event (0/N), so
    they cannot leak into the token sum; `summarize()` sums the raw `estimated_tokens_saved`
    field only. **One real defect found (not a dedup issue): the per-event derivation is
    inconsistent across delegates** — grok `delegate.py:602` uses `parent_tokens*3 - out`
    and devin `delegate.py:1352` uses `max(parent_tokens, delegate_input_tokens)*3` (both
    apply a ×3 factor, though on different bases), but kimi `delegate.py:825` uses bare
    `parent_tokens - delegate_output_tokens` (no ×3). This structurally under-counts kimi's
    savings vs devin/grok and makes cross-delegate `tokens_saved` comparisons apples-to-
    oranges. Verdict: **figures are directionally right (devin >> kimi) but the absolute
    numbers and any cross-delegate ratio are not trustworthy until the ×3 factor is
    reconciled.** Follow-up (separate work-order, NOT done here per read-only guardrail):
    standardize the estimated_tokens_saved formula across all three wrappers.
    **IMPLEMENTED 2026-07-01:** ×3 standardization deployed forward-only via a shared `tokens_saved.py` helper (K=3 ratified); each delegate vendors a byte-identical copy; historical events are unchanged; a one-time step in each series at cutover is expected and intended. Reference: `docs/workorder_standardize_tokens_saved_formula_20260701.md`.
- **R6 — Audit-only on devin-only modules.** grep for wiring; remove only provably-dead
  code. Lowest priority, after a test harness exists.

### 6.3 Revised sequencing
R3 (now) → R1 → R5 → R4 (experiment) → R2 (only if justified by a drift bug + tests) → R6.

### 6.4 Where the reviewers disagreed and how it was resolved
Mechanism of fragmentation: advisor said "fallback bug + 3 resolvers"; kimi said "intentional
per-repo, fallback unreachable because wrapper passes --repo-root." Resolved by reading
`delegate.py`: there is no `--repo-root` arg, the subprocess self-resolves, so BOTH the
non-git fallback AND per-repo scatter occur. The agreed fix (global aggregator that preserves
attribution + add the missing passthrough) satisfies both critiques.

### 6.5 Net change from v1
Down-scoped and de-risked: P2 shared-lib is deferred/narrowed, grok is dormant not deprecated,
all delegate-reshaping is gated behind more data + an aggregator, and tests/rollback are now
prerequisites rather than afterthoughts. Only R3 (docs) is safe to ship immediately.
