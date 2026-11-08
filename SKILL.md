---
name: delegate-skill
description: "Route bounded tasks to the right lane: Codex (builds, fan-outs), Devin (unknown scope, browser/UI, sandbox), Grok (small mechanical work only), Jev (typed classification)."
triggers:
  - which delegate should I use
  - delegate this task
  - use a subagent for this
  - should I use devin
  - should I use grok
  - codex fanout
  - fan out to codex
allowed-tools:
  - Bash
  - Read
---

# Delegate routing

Ladders, quota fallbacks and review slots live in `~/.claude/CLAUDE.md` ("Cheapest lane that works") and `~/.config/crss/staffing.md`. Read those first; this file only holds the commands. Always scope the task: goal, constraints, acceptance check, output format.

## Picking the right delegate and model

| Task | Lane | Command |
|---|---|---|
| Build / mechanical edit with a check | Codex `gpt-6.1-terra` low (sol61 high for hard uncovered work) | `codex exec -m gpt-6.1-terra -c model_reasoning_effort=low -c service_tier=priority --cd <dir> --sandbox workspace-write "<task>" </dev/null` |
| Codex quota-out | Haiku low builds (Haiku high after a failed check) | Agent tool, `model: haiku` |
| Unknown scope, browser/UI, sandbox | Devin | `devin-delegate --task "..." --workspace <trusted git repo>` |
| Small mechanical work, never review | Grok | `grok -p "<task>" --cwd <dir> --always-approve --no-subagents </dev/null` |
| Typed decision (route/triage/pick-one), non-private text | Jev | `jev-delegate --state "..." --question choice --instructions "..." --options "a=...,b=...,unclear=none fits" --min-confidence 0.85`; exit 5 or 3 means escalate to Haiku |
| Review | gpt-6.1-sol or Claude; never Grok | see staffing.md |

Judge output, not price: a weak result is redone on a stronger lane without asking. Anything user-facing (UI, copy, API design) needs Sonnet or Opus taste, never raw Devin or Haiku.

## Devin

`devin-delegate` is a thin wrapper over `devin -p`: no fallback, no history. Check it with `devin-delegate --check`.
- Exit 126: untrusted workspace or auth failure. Do not retry; trust the directory (Devin `trusted_workspaces.json`) or run `devin auth login`.
- Exit 124: timed out (`DEVIN_DELEGATE_TIMEOUT`, default 600 s). Treat as failure and move down the ladder.
- Verify its output; it is unreviewed.

## Grok and Jev

Grok: `grok login` to authenticate; never read `~/.grok/auth.json`. Jev: a classifier, not a reasoner; always offer an unclear option; never send credentials, private memory, broker or crypto data.
