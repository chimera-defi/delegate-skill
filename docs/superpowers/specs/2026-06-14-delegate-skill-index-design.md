# Delegate Skill Index — Design Spec

**Date:** 2026-06-14  
**Status:** Approved

---

## Problem

Four AI delegation skills exist as separate repos (devin-delegate, kimi-delegate, grok-delegate, spark). There is no single place a user or agent can pull in all four with one command. Each skill also has inconsistent maturity: grok-delegate is missing triggers, a setup script, bypass detection, and hooks that the others have.

---

## Goal

Turn the `delegate-skill` repo into a thin index hub that:
1. Installs all four delegate skills via a single `setup.sh`
2. Provides cross-agent routing guidance (CLAUDE.md / AGENTS.md / GEMINI.md)
3. Is installable as a Claude plugin (`.claude-plugin/` manifest)
4. Fixes gaps in grok-delegate so all four skills have consistent maturity

---

## Skills in Scope

| Skill | Source Repo | Purpose |
|-------|-------------|---------|
| `devin-delegate` | `workspace/devin-delegate` | Browser, sandbox impl, debugging via Devin |
| `kimi-delegate` | `workspace/kimi-delegate-skill` | Cheap bounded research/review via Kimi |
| `grok-delegate` | `workspace/grok-delegate` | Multi-file refactor / large codebase impl via Grok Build |
| `spark` | `gstack` (via symlink) | Local Codex write-mode implementation delegate |

`pair-agent` excluded — it's browser sharing, not AI delegation.

---

## Architecture

### Repository Structure

```
delegate-skill/
├── .claude-plugin/
│   ├── plugin.json          # Claude plugin manifest
│   └── marketplace.json     # Future marketplace listing
├── skills/
│   ├── devin-delegate/      # symlink → ~/.agents/skills/devin-delegate
│   ├── kimi-delegate/       # symlink → ~/.agents/skills/kimi-delegate
│   ├── grok-delegate/       # symlink → ~/.agents/skills/grok-delegate
│   └── spark/               # symlink → gstack spark skill
├── docs/
│   └── superpowers/specs/   # Design specs (this file)
├── CLAUDE.md                # Claude agent routing
├── AGENTS.md                # Codex / OpenAI agent routing
├── GEMINI.md                # Gemini agent stub
├── README.md                # Human-readable index + install guide
└── setup.sh                 # One-shot installer for all four skills
```

### setup.sh Responsibilities

1. Init git repo if not already one
2. For each of devin-delegate, kimi-delegate, grok-delegate:
   - Check if already installed at `~/.agents/skills/<name>`; if so, skip clone
   - If not installed, clone from the canonical GitHub URL (or local path for grok until it ships):
     - devin-delegate: `https://github.com/chimera-defi/devin-delegate.git`
     - kimi-delegate: `https://github.com/chimera-defi/kimi-delegate-skill.git`
     - grok-delegate: no public remote yet — clone from `~/workspace/grok-delegate` if it exists, otherwise warn and skip
   - Run the skill's own `setup.sh` to install binaries and configure hooks
   - Create `skills/<name>` symlink pointing to the installed location
3. Check if gstack is installed; if so, symlink `skills/spark` to the gstack spark skill
4. Run `devin-delegate --check`, `kimi-delegate --check`, `grok-delegate --check` and report status
5. Print a routing summary

> **Note:** grok-delegate has no public GitHub remote as of 2026-06-14. Until it is published, `setup.sh` performs a local clone from `~/workspace/grok-delegate` or skips with a warning. Push grok-delegate to GitHub and update the URL before sharing this index publicly.

### Routing Files

**CLAUDE.md** and **AGENTS.md** both contain a `<!-- delegate-skill:begin -->` block with:
- A delegation routing decision table (when to use which delegate)
- Mandatory wrapper rules (no raw CLI calls)
- Quick-start commands for each skill

**GEMINI.md** is a brief stub pointing to AGENTS.md.

Routing decision table:

| Task type | Delegate |
|-----------|---------|
| Browser, UI, screenshot, sandbox implementation | `devin-delegate` |
| Cheap search / summarize / draft / review | `kimi-delegate` |
| Multi-file refactor, large-codebase implementation | `grok-delegate` |
| Local Codex write-mode implementation | `spark` |
| Unknown / orchestration | Start with `kimi-delegate` for scoping, then escalate |

### Plugin Manifest

`.claude-plugin/plugin.json` follows the superpowers format:

```json
{
  "name": "delegate-skill",
  "description": "Index of AI delegation skills: devin, kimi, grok, spark",
  "version": "1.0.0",
  "author": { "name": "Chimera", "email": "chimera_defi@protonmail.com" },
  "homepage": "https://github.com/chimericlabs/delegate-skill",
  "license": "MIT"
}
```

---

## Grok-Delegate Fixes

grok-delegate is missing infrastructure that kimi-delegate and devin-delegate have. These gaps must be closed before the index ships.

| Gap | Fix |
|-----|-----|
| No `triggers:` in SKILL.md | Add trigger list matching grok-delegate usage patterns |
| No `setup.sh` | Add root-level `setup.sh` that installs binary, links to `~/.agents/skills/`, runs `env_check.py` |
| No `detect_bypass.py` | Port kimi-delegate's `detect_bypass.py` with opencode/grok-specific patterns |
| No `.githooks/` | Add `commit-msg` hook matching devin-delegate's attribution format |
| No `fallback.py` | Add minimal fallback script (Codex) matching kimi-delegate pattern |

---

## Testing Plan

### E2E Status (as of 2026-06-14)

| Skill | Env Check | E2E Delegation | Notes |
|-------|-----------|----------------|-------|
| kimi-delegate | ✅ ok | ✅ PASSED | Listed workspace dirs correctly |
| devin-delegate | ✅ ok | ✅ PASSED | Listed workspace dirs via Devin wrapper |
| grok-delegate | ✅ ok | ❌ Auth error | xAI OAuth not configured on this host — expected behavior, not a code bug |
| spark | ✅ ok | N/A | CLI skill; codex v0.139.0 available; invoked via `/spark` in Claude Code |

### Remaining Verification (before shipping)

1. Run `devin-delegate --check` → all_ok: true
2. Run `kimi-delegate --check` → all_ok: true
3. Run `grok-delegate --check` → all_ok: true (run from a git repo; requires xAI OAuth setup)
4. Run `setup.sh` from a clean state and verify all four skills install
5. Verify `skills/` symlinks resolve to correct locations
6. Verify CLAUDE.md and AGENTS.md contain the routing block
7. Verify `.claude-plugin/plugin.json` is valid JSON

---

## What Is Explicitly Out of Scope

- Extracting gstack into this repo (gstack remains its own project; spark is referenced via symlink)
- Adding pair-agent (browser sharing, not delegation)
- Making grok-delegate feature-complete with devin-delegate (we add the critical missing pieces only)
- CI/CD pipelines for this index repo
