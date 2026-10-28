# delegate-skill — Agent Routing (Codex / OpenAI / ChatGPT)

> This file provides routing guidance for non-Claude agents. For Claude Code, see CLAUDE.md.

<!-- delegate-skill:begin -->
## AI Delegation Routing

> Canonical routing table, model/delegate ratings, and fallback rules live in `SKILL.md`.
> This block mirrors the routing table for non-Claude agents that do not auto-load the skill.
> Keep the two in sync when routing changes. For ratings and escalation rules see
> `SKILL.md` § "Picking the right delegate and model".

Spark/Codex is preferred for local mechanical implementation. `devin-delegate` is the
general implement/review workhorse (browser/sandbox is one of its capabilities). Kimi is retired (2026-10-25).

As of **2026-10-27**, the OpenCode-based `grok-delegate` wrapper and `opencode` CLI are uninstalled from this host. Use the official xAI Grok CLI directly: `grok` **v1.0.70**. Grok is active for second-opinion / research review from a different model family and large-codebase implementation when asked.

Headless one-shot: `grok -p "<scoped prompt>" --cwd <dir> </dev/null`. Optional: `-m grok-4.7` or `-m grok-4.7-build-fast`, `--output-format json`, `--max-turns N`. Authenticate with `grok login`; credentials are in `~/.grok/auth.json` (never read or print them).

Health check: `grok -p "Reply with exactly: GROK_OK" </dev/null`. Never bypass the **Devin** wrapper: use `devin-delegate`, which provides envelope, fallback, and telemetry. `grok` is called directly by design.

| Task type | Delegate | Command |
|-----------|----------|---------|
| General implementation / review / debug (workhorse) | `devin-delegate` | `devin-delegate --task "..." --workspace /path/to/repo` |
| Browser, UI, screenshot, sandbox (a devin capability) | `devin-delegate` | `devin-delegate --task "..." --workspace /path/to/repo` |
| Local mechanical implementation / transformation / migration | `spark` / Codex Spark | `codex exec -m gpt-6.1-sol -c model_reasoning_effort=high -c service_tier=priority ... </dev/null` (or `codex-spark --task`) |
| Fast typed **decision / classification** (route, triage, tag, yes/no, pick-one-of-N) over non-private text; ~250 ms, ~$0.02 per 1k decisions | `jev-delegate` (TypeSafe Jev System One API) | `jev-delegate --state "..." --question choice --instructions "..." --options "a=...,b=...,unclear=none fits" --min-confidence 0.85` |
| Cheap **small read-only** search / summarize / draft / review | Spark/Codex bounded subagent | scoped read-only subagent call |
| Second-opinion / research review from a different model family; large-codebase implementation when asked | `grok` | `grok -p "<scoped prompt>" --cwd <dir> </dev/null` |
| Unknown / orchestration | `devin-delegate` (workhorse) | `devin-delegate --task "scope: ..."` |

### Rules

- **Never bypass the Devin wrapper.** Use `devin-delegate` for envelope, fallback, and telemetry; never call `devin` directly. `grok` is called directly by design.
- **Always include scope** in the task prompt: goal, constraints, acceptance checks, expected output format.
- **Devin auth errors exit 126** — do not auto-retry. Print resume steps for the user. For Grok auth, use `grok login`.
- **Jev is a classifier, not a reasoner.** Always offer an unclear/none option and gate with `--min-confidence`; exit 5 (below threshold) or 3 (call failed) -> escalate to a Haiku lane or the orchestrator. Never send credentials, private memory, broker/portfolio or crypto data (self-serve keys have standard retention). Usage, eval numbers and slots: crss `references/jev-delegate.md`.

### Quick-start

```bash
# Check all delegates are healthy
devin-delegate --check
grok -p "Reply with exactly: GROK_OK" </dev/null

# Run setup if Devin/Spark binaries are missing
bash setup.sh
```
<!-- delegate-skill:end -->

<!-- token-reduce:begin -->
## Token-Reduce Routing

- If file location is unknown, your first discovery command MUST be `./skills/token-reduce/scripts/token-reduce-paths.sh topic words`.
- Use the user’s literal nouns from the prompt in that first query (feature name, file stem, hook name, symbol).
- Use `./skills/token-reduce/scripts/token-reduce-snippet.sh topic words` only if one ranked excerpt is needed after the path list.
- Do not start repo discovery with `find .`, `ls -R`, `grep -R`, `rg --files .`, or broad `Glob` patterns.
- Use scoped `rg -g` and targeted reads only after helper output.
<!-- token-reduce:end -->
