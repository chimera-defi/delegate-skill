# delegate-skill

Workspace for building and iterating on Claude Code delegate skills.

## Available skills (all global)

All gstack, gbrain, token-reduce, devin-delegate, kimi-delegate, grok-delegate,
spark, pair-agent, and other global skills are available via slash commands.

## Skill routing

- Building/iterating on a skill: use `/spec` to define it, `/review` to check it
- Delegate orchestration: use `devin-delegate`, `kimi-delegate`, `grok-delegate` wrappers
- Token efficiency: use `/token-reduce` first before broad repo scans
- Save progress: `/context-save` / `/context-restore`

<!-- delegate-skill:begin -->
## AI Delegation Routing

`devin-delegate` is the general implement/review workhorse (browser/sandbox is one of its
capabilities). `kimi-delegate` is for cheap, small, read-only tasks. `grok-delegate` is
**dormant** — revival gate: ≥5 successful calls + a documented devin failure on a large repo.

| Task type | Delegate | Command |
|-----------|----------|---------|
| General implementation / review / debug (workhorse) | `devin-delegate` | `devin-delegate --task "..." --workspace /path/to/repo` |
| Browser, UI, screenshot, sandbox (a devin capability) | `devin-delegate` | `devin-delegate --task "..." --workspace /path/to/repo` |
| Cheap **small read-only** search / summarize / draft / review | `kimi-delegate` | `kimi-delegate --task "..."` |
| Local Codex write-mode implementation | `spark` | `/spark` (Claude Code skill) |
| Multi-file refactor on a very large codebase (DORMANT) | `grok-delegate` | `grok-delegate --task "..."` |
| Unknown / orchestration | `devin-delegate` (workhorse); if clearly cheap+small, `kimi-delegate` | `devin-delegate --task "scope: ..."` |

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
<!-- delegate-skill:end -->
