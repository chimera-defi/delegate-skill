# delegate-skill

Workspace for building and iterating on Claude Code delegate skills.

## Available skills (all global)

All gstack, gbrain, token-reduce, devin-delegate, grok-delegate, spark, pair-agent,
and other global skills are available via slash commands; Kimi is optional compatibility.

## Skill routing

- Building/iterating on a skill: use `/spec` to define it, `/review` to check it
- Delegate orchestration: use Spark/Codex for local mechanical work and `devin-delegate` for general work
- Token efficiency: use `/token-reduce` first before broad repo scans
- Save progress: `/context-save` / `/context-restore`

<!-- delegate-skill:begin -->
## AI Delegation Routing

Spark/Codex is preferred for local mechanical implementation. `devin-delegate` is the
general implement/review workhorse (browser/sandbox is one of its capabilities). Kimi is
optional compatibility for cheap, small, read-only tasks. `grok-delegate` is
**dormant** — revival gate: ≥5 successful calls + a documented devin failure on a large repo.

| Task type | Delegate | Command |
|-----------|----------|---------|
| General implementation / review / debug (workhorse) | `devin-delegate` | `devin-delegate --task "..." --workspace /path/to/repo` |
| Browser, UI, screenshot, sandbox (a devin capability) | `devin-delegate` | `devin-delegate --task "..." --workspace /path/to/repo` |
| Local mechanical implementation / transformation / migration | `spark` / Codex Spark | `/spark` (Claude Code skill) |
| Cheap **small read-only** search / summarize / draft / review | Spark/Codex bounded subagent | scoped read-only subagent call |
| Multi-file refactor on a very large codebase (DORMANT) | `grok-delegate` | `grok-delegate --task "..."` |
| Unknown / orchestration | `devin-delegate` (workhorse) | `devin-delegate --task "scope: ..."` |

### Rules

- **Never call delegates directly** (`opencode`, `pi --provider kimi-coding`, `devin`) — always use the wrapper scripts. Wrappers inject the envelope, fallback chain, and telemetry.
- **Always include scope** in the task prompt: goal, constraints, acceptance checks, expected output format.
- **Auth errors exit 126** — do not auto-retry. Print resume steps for the user.

### Quick-start

```bash
# Check all delegates are healthy
devin-delegate --check
kimi-delegate --check
grok-delegate --check

# Run setup if binaries are missing
bash setup.sh
```

> For model and delegate ratings, escalation permissions, and fallback rules see `~/.claude/skills/delegate-skill/SKILL.md` § "Picking the right delegate and model".
<!-- delegate-skill:end -->
