# delegate-skill

One-stop index for AI delegation skills, with direct access to the official xAI Grok CLI.

## Install

```bash
git clone https://github.com/chimera-defi/delegate-skill
cd delegate-skill
bash setup.sh
```

`setup.sh` still contains legacy Grok wrapper installation and routing. Its migration
to the direct CLI is proposed separately; it is not the Grok installation path.

## Skills

| Skill | Purpose | Source |
|-------|---------|--------|
| `devin-delegate` | Browser, UI, screenshot, sandbox implementation | [chimera-defi/devin-delegate](https://github.com/chimera-defi/devin-delegate) |
| `grok` | Small mechanical work (never review) | Official xAI Grok CLI v1.0.70 (called directly) |
| `spark` / `codex-spark` | Local Codex Spark write-mode implementation | native GStack `/spark` when installed, otherwise the checked-in `codex-spark` adapter |

## Routing

Canonical routing table (with rules, fallback, auth, and latency notes) lives in
[`SKILL.md`](SKILL.md). Quick summary:

| Task | Use |
|------|-----|
| General implement / review / debug (workhorse) | `devin-delegate` |
| Browser / UI / screenshot / sandbox (a devin capability) | `devin-delegate` |
| Local mechanical implementation / transformation / migration | Spark/Codex |
| Cheap **small read-only** search / summarize / review | Spark/Codex bounded subagent |
| Small mechanical work (never review) | `grok` directly |
| Unclear scope | `devin-delegate` (workhorse) |

As of **2026-10-27**, the OpenCode-based `grok-delegate` wrapper and `opencode` CLI are uninstalled from this host. Use the official xAI Grok CLI directly: `grok` **v1.0.70**. Grok does small mechanical work only and never reviews (operator 2026-11-01: not trusted to review).

Headless one-shot: `grok -p "<scoped prompt>" --cwd <dir> </dev/null`. Optional: `-m grok-4.7` or `-m grok-4.7-build-fast`, `--output-format json`, `--max-turns N`. Authenticate with `grok login`; credentials are in `~/.grok/auth.json` (never read or print them).

Health check: `grok -p "Reply with exactly: GROK_OK" </dev/null`. Never bypass the **Devin** wrapper: use `devin-delegate`, which provides envelope, fallback, and telemetry. `grok` is called directly by design.

## Superpowers & GStack integration

`setup.sh` wires delegate-skill into your global agent environment automatically:

- **`~/.claude/skills/delegate-skill`** → symlinked so Claude Code loads the skill in every workspace
- **`~/.claude/CLAUDE.md`** → routing block injected so every session can route to delegates without opening this repo
- **SKILL.md** → triggers auto-load: say "delegate this task" or "which delegate should I use" and routing is invoked

### With Superpowers

`superpowers:subagent-driven-development` dispatches fresh subagents per task. Those subagents can use delegate skills for bounded work:

- Implementation step needing a browser → `devin-delegate`
- Review or research step → Spark/Codex bounded subagent; use Devin when browser/sandbox access is required
- Small mechanical step, when asked → `grok` directly

Delegates keep subagent context small: only the result summary enters the parent context.

### With GStack

GStack may include `/spark` (Codex write-mode) as a built-in. When that native skill is
missing, `setup.sh` installs `codex-spark`, an explicit Codex CLI adapter that preserves
the same model selection and makes availability observable:

```bash
codex-spark --check
codex-spark --task "bounded task" --workspace /path/to/repo
```

`delegate-skill` extends either Spark entrypoint with:

- `devin-delegate` — real browser, shell, debugging sandbox
- `grok` directly — small mechanical work only; never review

Install both to get the full execution layer.

## Claude plugin

Install as a Claude Code plugin to make all skills available via slash commands:

```bash
claude plugin install .
```

## Agent compatibility

| Agent | Routing file |
|-------|-------------|
| Claude Code | CLAUDE.md |
| Codex / ChatGPT | AGENTS.md |
| Gemini CLI | GEMINI.md |
