---
name: task-add-model-selection-framework
description: Improve SKILL.md with a rating-based model/delegate selection framework — cost, intelligence, taste, availability — with fallback rules and standing escalation permission
metadata:
  type: project
---

## Task

Add a **"Picking the right delegate and model"** section to `SKILL.md` (and mirror a condensed version in `CLAUDE.md`/`AGENTS.md` if they reference routing). The current routing table tells you *what* to use for a task type but not *how to choose when the preferred option is unavailable*, *when to escalate*, or *which Claude model to pick inside subagents/Agent tool calls*.

## Why

Delegates are not always up. devin requires active auth; grok is dormant; kimi can drift. Without ratings and fallback rules, callers get stuck when the preferred delegate is unavailable or returns low-quality output. This adds a principled framework: rate each option on cost, intelligence, taste, and availability, then define escalation and fallback rules so callers never block.

## Content to add

Insert this as a new `## Picking the right delegate and model` section in `SKILL.md`, after the current routing table and before the Rules section:

---

### Ratings

Higher = better. **Cost** = cheap/rate-limit-friendly (inverse of price). **Intelligence** = how hard a problem you can hand it unsupervised. **Taste** = output quality, code aesthetics, API design, copy. **Availability** = how reliably it's reachable without auth errors or quota issues.

**External delegates**

| delegate | cost | intelligence | taste | availability | notes |
|----------|------|--------------|-------|--------------|-------|
| devin | 4 | 8 | 6 | 6 | Auth-sensitive (exit 126 = re-auth required). Browser/sandbox built in. |
| kimi | 9 | 4 | 4 | 7 | Read-only, light auth. Fast for cheap parallel research. |
| grok | 5 | 7 | 5 | 0 | **Dormant** — revival gate not met. Do not route here. |
| spark/codex | 8 | 6 | 5 | 9 | Local, always-on. Ground-floor fallback for implementation. |

**Claude models** (for `model:` parameter in Agent tool / Workflow calls)

| model | cost | intelligence | taste |
|-------|------|--------------|-------|
| claude-haiku-4-5 | 9 | 4 | 4 |
| claude-sonnet-4-6 | 6 | 7 | 7 |
| claude-opus-4-7 | 3 | 9 | 8 |

### How to apply

- **Defaults, not ceilings.** You have standing permission to escalate: if a cheaper delegate's output doesn't meet the bar, retry or redo with a smarter one without asking. Judge the output, not the price tag. Escalating costs less than shipping mediocre work.
- **Availability overrides preference.** If the preferred delegate is down (auth error / exit 126), fall back immediately — don't wait for the user. Fallback chain: devin → spark → direct Claude (sonnet). For research: kimi → direct Claude.
- **Cost is a tie-breaker only.** When axes conflict for anything that ships: intelligence > taste > cost.
- **Bulk/mechanical work** (clear-spec implementation, data transformation, migrations): spark/codex — cheap, fast, local, always available.
- **Anything user-facing** (UI, copy, API design) needs taste ≥ 7: use devin or claude-sonnet-4-6 / claude-opus-4-7. Never kimi or claude-haiku-4-5 for shipped output.
- **Reviews and adversarial critique**: claude-opus-4-7 or `/gstack-claude challenge`. Optionally add spark/codex as an independent second opinion.
- **Research / summarize / small diffs**: kimi first (cheapest) → spark if kimi is unavailable.
- **Never use claude-haiku-4-5 for anything that ships.** Reserve it for pure triage/classification steps inside larger workflows.
- **Claude models only in Agent tool calls.** The `model:` parameter does not accept external delegates. For mechanical steps needing a non-Claude model, spawn a thin Sonnet wrapper whose prompt is to write a self-contained codex prompt and run `codex exec` via Bash.
- **Never bypass wrappers.** Raw calls skip envelope, fallback, and telemetry — always use `devin-delegate`, `kimi-delegate`, `grok-delegate` binaries.

---

## Implementation notes

- Keep the existing routing table — this section adds *why* and *what to do when things go wrong*, not a replacement.
- The availability column makes it explicit that grok is 0 (dormant) and spark is 9 (always-on) — this should reinforce the existing fallback language.
- Check if `CLAUDE.md` and `AGENTS.md` have their own routing summaries and keep them consistent — at minimum add a pointer to `SKILL.md` for the full framework.
- Bump version in SKILL.md frontmatter (currently 1.0.0 → 1.1.0).
- After editing, run `bash setup.sh` if it touches anything setup installs (probably not for SKILL.md-only changes, but verify).

## Workflow

**Before writing anything:** call `advisor()` with no parameters. Brief it on what you've read in SKILL.md, CLAUDE.md, and AGENTS.md, and ask it to review the proposed section for completeness, consistency with the existing skill, and anything that would make the routing worse. Give the advisor's feedback serious weight — if it contradicts the spec here, surface the conflict rather than silently picking one.

**After drafting the changes:** call `advisor()` again before committing. Show it the full diff and ask: does this make the delegate routing better or worse? Are the ratings defensible? Is the fallback chain complete? Only commit after the advisor signs off or you've addressed its concerns.

## How to apply

**Why:** Currently callers block or ask the user when a delegate is unavailable. The framework + fallback chain + escalation permission makes the skill self-healing.

**Constraints:** Additive only — don't change the routing table or existing rules, just add the new section and update version.
