# Delegate Skill Index Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `delegate-skill` into a thin index hub that installs all four delegate skills (devin, kimi, grok, spark) via a single `setup.sh` and provides cross-agent routing guidance.

**Architecture:** Fix gaps in grok-delegate first, then build the index repo: symlinks in `skills/`, a Claude plugin manifest in `.claude-plugin/`, routing docs (CLAUDE.md/AGENTS.md/GEMINI.md), a README, and a `setup.sh` that clones/links each skill.

**Tech Stack:** Bash (setup.sh, hooks), Python 3 (detect_bypass.py), JSON (plugin manifest), Markdown (routing docs). No new external dependencies.

---

## File Map

### grok-delegate (workspace/grok-delegate)

| Action | Path | Purpose |
|--------|------|---------|
| Modify | `SKILL.md` | Add `triggers:` frontmatter so agents auto-invoke the skill |
| Create | `setup.sh` | Install binary, link to `~/.agents/skills/`, run env_check |
| Create | `scripts/detect_bypass.py` | Detect raw `opencode` calls bypassing the wrapper |
| Create | `scripts/repo_scan.py` | Shared helper used by detect_bypass.py |
| Create | `scripts/install_git_hooks.py` | Configure `.githooks` path in git config |
| Create | `.githooks/commit-msg` | Enforce commit format with agent attribution |

### delegate-skill (workspace/delegate-skill)

| Action | Path | Purpose |
|--------|------|---------|
| Create | `.claude-plugin/plugin.json` | Claude plugin manifest |
| Create | `.claude-plugin/marketplace.json` | Future marketplace listing |
| Create | `skills/` | Directory for symlinks to each delegate skill |
| Create | `setup.sh` | One-shot installer for all four skills |
| Modify | `CLAUDE.md` | Add `<!-- delegate-skill:begin -->` routing block |
| Create | `AGENTS.md` | Codex/OpenAI routing (same block as CLAUDE.md) |
| Create | `GEMINI.md` | Gemini stub pointing to AGENTS.md |
| Create | `README.md` | Human-readable index and install guide |

---

## Task 1: Add triggers to grok-delegate SKILL.md

**Files:**
- Modify: `workspace/grok-delegate/SKILL.md`

- [ ] **Step 1: Edit SKILL.md to add triggers field**

Replace the frontmatter block (the `---` delimited section at the top of the file) with:

```yaml
---
name: grok-delegate
preamble-tier: 4
version: 0.1.1
description: "Delegate bounded coding tasks to Grok Build model via OpenCode integration with envelope/fallback telemetry."
triggers:
  - delegate to Grok
  - grok-delegate
  - use Grok for a bounded task
  - multi-file refactor via Grok
  - large codebase implementation
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
---
```

The rest of the file is unchanged.

- [ ] **Step 2: Verify SKILL.md parses as valid YAML frontmatter**

```bash
python3 -c "
import re, sys
text = open('workspace/grok-delegate/SKILL.md').read()
m = re.match(r'^---\n(.+?)\n---', text, re.DOTALL)
assert m, 'no frontmatter found'
import yaml
data = yaml.safe_load(m.group(1))
assert 'triggers' in data, 'triggers missing'
assert len(data['triggers']) >= 1, 'triggers empty'
print('OK:', data['triggers'])
"
```

Expected output: `OK: ['delegate to Grok', 'grok-delegate', ...]`

- [ ] **Step 3: Commit**

```bash
cd workspace/grok-delegate
git add SKILL.md
git commit -m "feat(skill): add triggers frontmatter to SKILL.md [Agent: Claude Sonnet 4.6]

Co-authored-by: Chimera <chimera_defi@protonmail.com>"
```

---

## Task 2: Add setup.sh to grok-delegate

**Files:**
- Create: `workspace/grok-delegate/setup.sh`
- Create: `workspace/grok-delegate/scripts/install_git_hooks.py`

- [ ] **Step 1: Create setup.sh**

Create `workspace/grok-delegate/setup.sh`:

```bash
#!/usr/bin/env bash
# Install grok-delegate wrappers, links, and run environment verification.
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$SKILL_ROOT/scripts"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$BIN_DIR" "$HOME/.agents/skills" "$HOME/.openclaw/skills" "${CODEX_HOME:-$HOME/.codex}/skills"

# Enable local hooks for attribution/commit format checks.
if [ -d "$SKILL_ROOT/.githooks" ]; then
  git -C "$SKILL_ROOT" config core.hooksPath .githooks || true
fi

# Install canonical skill links used by agent runtimes.
ln -sfn "$SKILL_ROOT" "$HOME/.agents/skills/grok-delegate"
ln -sfn "$HOME/.agents/skills/grok-delegate" "$HOME/.openclaw/skills/grok-delegate"
ln -sfn "$SKILL_ROOT" "${CODEX_HOME:-$HOME/.codex}/skills/grok-delegate"

# Install grok-delegate binary wrapper.
cat > "$BIN_DIR/grok-delegate" <<WRAP
#!/usr/bin/env bash
exec "$SCRIPTS/delegate.py" "\$@"
WRAP
chmod +x "$BIN_DIR/grok-delegate"

echo "Linked grok-delegate -> $SCRIPTS/delegate.py"

# Run environment check to confirm everything is wired.
echo ""
echo "Running env_check..."
python3 "$SCRIPTS/env_check.py" && echo "env_check: OK" || echo "env_check: WARNINGS (see above)"
```

Make it executable:

```bash
chmod +x workspace/grok-delegate/setup.sh
```

- [ ] **Step 2: Create install_git_hooks.py**

Create `workspace/grok-delegate/scripts/install_git_hooks.py`:

```python
#!/usr/bin/env python3
"""Configure git to use .githooks for grok-delegate."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    hooks_dir = repo_root / ".githooks"
    if not hooks_dir.is_dir():
        print(f"ERROR: .githooks directory not found at {hooks_dir}", file=sys.stderr)
        return 1
    result = subprocess.run(
        ["git", "-C", str(repo_root), "config", "core.hooksPath", ".githooks"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: {result.stderr.strip()}", file=sys.stderr)
        return result.returncode
    print(f"git hooks configured: {hooks_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```bash
chmod +x workspace/grok-delegate/scripts/install_git_hooks.py
```

- [ ] **Step 3: Run setup.sh and verify output**

```bash
cd workspace/grok-delegate
bash setup.sh
```

Expected output (contains):
```
Linked grok-delegate -> .../scripts/delegate.py
Running env_check...
✓ All checks passed!
env_check: OK
```

Also verify the binary was installed:
```bash
ls -la ~/.local/bin/grok-delegate
grok-delegate --check 2>&1 | grep -E "all_ok|ok"
```

Expected: `"all_ok": true` in the JSON output.

- [ ] **Step 4: Commit**

```bash
cd workspace/grok-delegate
git add setup.sh scripts/install_git_hooks.py
git commit -m "feat(infra): add setup.sh and install_git_hooks.py [Agent: Claude Sonnet 4.6]

Co-authored-by: Chimera <chimera_defi@protonmail.com>"
```

---

## Task 3: Add detect_bypass.py and repo_scan.py to grok-delegate

**Files:**
- Create: `workspace/grok-delegate/scripts/detect_bypass.py`
- Create: `workspace/grok-delegate/scripts/repo_scan.py`

- [ ] **Step 1: Create repo_scan.py**

Create `workspace/grok-delegate/scripts/repo_scan.py`:

```python
#!/usr/bin/env python3
"""Shared workspace repository discovery helpers."""
from __future__ import annotations

from pathlib import Path


def is_repo_root(path: Path) -> bool:
    return (path / ".git").exists()


def iter_workspace_repos(workspace_root: Path, include_worktrees: bool = True) -> list[Path]:
    repos: list[Path] = []
    seen: set[str] = set()
    root = workspace_root.resolve()

    def add_repo(path: Path) -> None:
        resolved_path = path.resolve()
        try:
            resolved_path.relative_to(root)
        except ValueError:
            return
        resolved = str(resolved_path)
        if resolved in seen:
            return
        seen.add(resolved)
        repos.append(path)

    for child in sorted(workspace_root.iterdir()):
        if not child.is_dir() or child.is_symlink():
            continue
        if is_repo_root(child):
            add_repo(child)
        if not include_worktrees:
            continue
        worktrees_root = child / ".worktrees"
        if not worktrees_root.is_dir():
            continue
        for worktree in sorted(worktrees_root.iterdir()):
            if worktree.is_dir() and not worktree.is_symlink() and is_repo_root(worktree):
                add_repo(worktree)
    return repos


def repo_label(repo: Path, workspace_root: Path) -> str:
    try:
        return repo.resolve().relative_to(workspace_root.resolve()).as_posix()
    except ValueError:
        return repo.name
```

- [ ] **Step 2: Create detect_bypass.py**

Create `workspace/grok-delegate/scripts/detect_bypass.py`:

```python
#!/usr/bin/env python3
"""Detect raw OpenCode calls that bypass the grok-delegate skill wrapper."""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from repo_scan import iter_workspace_repos, repo_label
except ModuleNotFoundError:
    import sys
    sys.path.append(str(Path(__file__).resolve().parent))
    from repo_scan import iter_workspace_repos, repo_label

# Pattern matching legitimate grok-delegate wrapper invocations.
DELEGATE_CMD_RE = re.compile(
    r"(?:^|\s)(?:\./)?(?:skills/grok-delegate/scripts/delegate\.py|grok-delegate)(?:\s|$)",
    re.IGNORECASE,
)

# Pattern matching raw opencode calls — only when actually invoked, not when
# the name appears as a path argument or inside a string literal.
GROK_SUBAGENT_RE = re.compile(
    r"(?:^|\s)opencode\b",
)


def is_false_positive_command(command: str) -> bool:
    """Return True if the command is an install/check, not a delegation bypass."""
    fp_patterns = [
        r"opencode\s+--version",
        r"opencode\s+--help",
        r"which\s+opencode",
        r"command\s+-v\s+opencode",
        r"#.*opencode",
        r"echo.*opencode",
    ]
    return any(re.search(p, command) for p in fp_patterns)


def collect_session_files(base: Path, cutoff_ts: float) -> list[Path]:
    files: list[Path] = []
    for path in base.rglob("*.jsonl"):
        try:
            if path.stat().st_mtime < cutoff_ts:
                continue
        except OSError:
            continue
        files.append(path)
    return files


def parse_bypasses_claude(path: Path) -> list[dict[str, Any]]:
    """Parse a Claude session JSONL file for raw opencode bypass calls."""
    bypasses: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return bypasses
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = event.get("message", {})
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "tool_use" or item.get("name") != "Bash":
                continue
            command = item.get("input", {}).get("command", "")
            if not isinstance(command, str):
                continue
            if is_false_positive_command(command):
                continue
            if GROK_SUBAGENT_RE.search(command) and not DELEGATE_CMD_RE.search(command):
                ts = event.get("timestamp", "")
                bypasses.append({
                    "source": "claude",
                    "session_file": str(path),
                    "command": command,
                    "timestamp": ts,
                })
    return bypasses


def detect_bypasses(
    workspace_root: Path,
    days: int,
    repo_filter: Path | None = None,
) -> dict[str, Any]:
    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_ts = cutoff_dt.timestamp()

    if repo_filter is not None:
        repo_paths = [repo_filter]
    else:
        repo_paths = iter_workspace_repos(workspace_root, include_worktrees=True)

    claude_sessions_root = Path.home() / ".claude" / "projects"
    session_files = collect_session_files(claude_sessions_root, cutoff_ts) if claude_sessions_root.exists() else []

    all_bypasses: list[dict[str, Any]] = []
    for session_file in session_files:
        hits = parse_bypasses_claude(session_file)
        all_bypasses.extend(hits)

    total_sessions = len(session_files)
    bypass_count = len(all_bypasses)
    bypass_rate = round(bypass_count / total_sessions * 100, 1) if total_sessions else 0.0

    return {
        "days": days,
        "total_sessions_scanned": total_sessions,
        "bypass_count": bypass_count,
        "bypass_rate_pct": bypass_rate,
        "bypasses": all_bypasses,
    }


def nudge_report(report: dict[str, Any]) -> str:
    count = report["bypass_count"]
    rate = report["bypass_rate_pct"]
    if count == 0:
        return "[grok-delegate] No bypass calls detected. Good hygiene!"
    lines = [
        f"[grok-delegate] BYPASS ALERT: {count} raw opencode call(s) detected ({rate}% of sessions).",
        "Use grok-delegate wrapper instead of calling opencode directly.",
        "Bypasses skip envelope, fallback, and telemetry.",
        "",
    ]
    for b in report["bypasses"][:5]:
        lines.append(f"  {b['timestamp']}: {b['command'][:80]}")
    if count > 5:
        lines.append(f"  ... and {count - 5} more")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect raw opencode calls bypassing grok-delegate.")
    parser.add_argument("--workspace-root", default=str(Path.home() / "workspace"))
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--nudge", action="store_true", help="Print human-readable nudge report")
    parser.add_argument("--watch", action="store_true", help="Continuously watch for bypasses")
    parser.add_argument("--watch-interval", type=int, default=60)
    parser.add_argument("--output", help="Write JSON report to file")
    parser.add_argument("--repo", help="Limit scan to a single repo path")
    args = parser.parse_args()

    repo_filter = Path(args.repo).resolve() if args.repo else None

    if args.watch:
        print("[grok-delegate] Watching for bypass calls (Ctrl+C to stop)...")
        prev = 0
        while True:
            report = detect_bypasses(Path(args.workspace_root).resolve(), args.days, repo_filter=repo_filter)
            current = report["bypass_count"]
            if current != prev:
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] bypasses={current} rate={report['bypass_rate_pct']}%")
                if current > 0:
                    print(nudge_report(report))
                prev = current
            try:
                time.sleep(args.watch_interval)
            except KeyboardInterrupt:
                print("\nWatch stopped.")
                return 0

    report = detect_bypasses(Path(args.workspace_root).resolve(), args.days, repo_filter=repo_filter)

    if args.nudge:
        print(nudge_report(report))
        return 0

    text = json.dumps(report, indent=2)
    print(text)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```bash
chmod +x workspace/grok-delegate/scripts/detect_bypass.py
```

- [ ] **Step 3: Verify detect_bypass runs and produces valid JSON**

```bash
cd workspace/grok-delegate
python3 scripts/detect_bypass.py --days 1 2>&1 | python3 -c "
import sys, json
data = json.load(sys.stdin)
assert 'bypass_count' in data
assert 'bypass_rate_pct' in data
print('OK: bypass_count =', data['bypass_count'])
"
```

Expected: `OK: bypass_count = 0` (no bypasses on a fresh machine)

Also verify the nudge flag:
```bash
python3 scripts/detect_bypass.py --nudge --days 1
```

Expected: `[grok-delegate] No bypass calls detected. Good hygiene!`

- [ ] **Step 4: Commit**

```bash
cd workspace/grok-delegate
git add scripts/detect_bypass.py scripts/repo_scan.py
git commit -m "feat(safety): add detect_bypass.py and repo_scan.py [Agent: Claude Sonnet 4.6]

Co-authored-by: Chimera <chimera_defi@protonmail.com>"
```

---

## Task 4: Add .githooks/commit-msg to grok-delegate

**Files:**
- Create: `workspace/grok-delegate/.githooks/commit-msg`

- [ ] **Step 1: Create .githooks directory and commit-msg hook**

```bash
mkdir -p workspace/grok-delegate/.githooks
```

Create `workspace/grok-delegate/.githooks/commit-msg`:

```bash
#!/usr/bin/env bash
set -euo pipefail

msg_file="${1:-}"
if [ -z "$msg_file" ] || [ ! -f "$msg_file" ]; then
  echo "ERROR: commit-msg hook expected a commit message file path." >&2
  exit 1
fi

header="$(sed -n '1p' "$msg_file")"

# Allow auto-generated merge/revert/fixup/squash commits.
case "$header" in
  Merge\ *|Revert\ *|fixup!\ *|squash!\ *)
    exit 0
    ;;
esac

header_pattern='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)\([a-z0-9._/-]+\): [^[:space:]].* \[Agent: .+\]$'

if ! printf '%s\n' "$header" | grep -Eq "$header_pattern"; then
  cat >&2 <<'EOF'
ERROR: Invalid commit header format.

Expected:
  type(scope): subject [Agent: <MODEL NAME>]

Example:
  feat(delegate): add multi-file refactor support [Agent: Grok Build]

Allowed types:
  feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
EOF
  exit 1
fi

parsed_trailers="$(git interpret-trailers --parse "$msg_file" || true)"
if ! printf '%s\n' "$parsed_trailers" | grep -Eiq '^Co-authored-by:\s+(Chimera|ChimeraDeFi)\s+<chimera_defi@protonmail\.com>$'; then
  cat >&2 <<'EOF'
ERROR: Missing required Co-authored-by trailer in commit message footer.

Add this trailer at the end of your commit message:
  Co-authored-by: Chimera <chimera_defi@protonmail.com>
EOF
  exit 1
fi

# Reminder if hooksPath is not configured; do not block commits.
hooks_path="$(git config --get core.hooksPath || true)"
if [ "$hooks_path" != ".githooks" ]; then
  echo "WARNING: Configure git hooks path with: git config core.hooksPath .githooks" >&2
fi
```

```bash
chmod +x workspace/grok-delegate/.githooks/commit-msg
```

- [ ] **Step 2: Activate the hooks via install_git_hooks.py**

```bash
cd workspace/grok-delegate
python3 scripts/install_git_hooks.py
```

Expected: `git hooks configured: .../grok-delegate/.githooks`

Verify:
```bash
git -C workspace/grok-delegate config core.hooksPath
```

Expected: `.githooks`

- [ ] **Step 3: Smoke-test the hook rejects a bad commit message**

```bash
cd workspace/grok-delegate
echo "bad commit message" > /tmp/test-commit-msg.txt
bash .githooks/commit-msg /tmp/test-commit-msg.txt
echo "exit code: $?"
```

Expected: Non-zero exit code with `ERROR: Invalid commit header format.`

- [ ] **Step 4: Commit**

```bash
cd workspace/grok-delegate
git add .githooks/
git commit -m "feat(infra): add commit-msg hook with agent attribution [Agent: Claude Sonnet 4.6]

Co-authored-by: Chimera <chimera_defi@protonmail.com>"
```

---

## Task 5: Create Claude plugin manifest

**Files:**
- Create: `delegate-skill/.claude-plugin/plugin.json`
- Create: `delegate-skill/.claude-plugin/marketplace.json`

- [ ] **Step 1: Create .claude-plugin directory and plugin.json**

```bash
mkdir -p /home/agents/workspace/delegate-skill/.claude-plugin
```

Create `delegate-skill/.claude-plugin/plugin.json`:

```json
{
  "name": "delegate-skill",
  "description": "Index of AI delegation skills: devin (browser/sandbox), kimi (cheap research), grok (large codebase), spark (local Codex). Install all four with setup.sh.",
  "version": "1.0.0",
  "author": {
    "name": "Chimera",
    "email": "chimera_defi@protonmail.com"
  },
  "homepage": "https://github.com/chimera-defi/delegate-skill",
  "license": "MIT"
}
```

- [ ] **Step 2: Create marketplace.json**

Create `delegate-skill/.claude-plugin/marketplace.json`:

```json
{
  "name": "delegate-skill",
  "short_description": "Install all four AI delegation skills in one command.",
  "categories": ["productivity", "delegation", "multi-agent"],
  "tags": ["devin", "kimi", "grok", "spark", "delegate", "subagent"],
  "install_command": "bash setup.sh",
  "requirements": {
    "devin-delegate": "https://github.com/chimera-defi/devin-delegate",
    "kimi-delegate": "https://github.com/chimera-defi/kimi-delegate-skill",
    "grok-delegate": "local (no public remote yet)",
    "spark": "via gstack"
  }
}
```

- [ ] **Step 3: Validate both files are valid JSON**

```bash
python3 -c "
import json, pathlib
for f in ['.claude-plugin/plugin.json', '.claude-plugin/marketplace.json']:
    data = json.loads(pathlib.Path(f).read_text())
    print('OK:', f, list(data.keys()))
"
```

Expected:
```
OK: .claude-plugin/plugin.json ['name', 'description', 'version', 'author', 'homepage', 'license']
OK: .claude-plugin/marketplace.json ['name', 'short_description', 'categories', 'tags', 'install_command', 'requirements']
```

- [ ] **Step 4: Commit**

```bash
cd /home/agents/workspace/delegate-skill
git add .claude-plugin/
git commit -m "feat(plugin): add Claude plugin manifest [Agent: Claude Sonnet 4.6]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Create skills/ symlinks

**Files:**
- Create: `delegate-skill/skills/devin-delegate` (symlink)
- Create: `delegate-skill/skills/kimi-delegate` (symlink)
- Create: `delegate-skill/skills/grok-delegate` (symlink)
- Create: `delegate-skill/skills/spark` (symlink)

- [ ] **Step 1: Create skills/ directory and symlinks**

```bash
mkdir -p /home/agents/workspace/delegate-skill/skills

# Devin and kimi install to ~/.agents/skills/ via their own setup.sh.
# Use those installed locations so symlinks survive on any machine.
# Fall back to workspace paths for grok (no remote yet).

ln -sfn "$HOME/.agents/skills/devin-delegate" /home/agents/workspace/delegate-skill/skills/devin-delegate
ln -sfn "$HOME/.agents/skills/kimi-delegate" /home/agents/workspace/delegate-skill/skills/kimi-delegate
ln -sfn /home/agents/workspace/grok-delegate /home/agents/workspace/delegate-skill/skills/grok-delegate

# Spark lives in gstack's skills directory.
SPARK_PATH="$HOME/.claude/skills/gstack/spark"
if [ -d "$SPARK_PATH" ]; then
  ln -sfn "$SPARK_PATH" /home/agents/workspace/delegate-skill/skills/spark
  echo "Linked spark -> $SPARK_PATH"
else
  echo "WARNING: gstack spark not found at $SPARK_PATH — skipping spark symlink"
fi
```

- [ ] **Step 2: Verify symlinks resolve**

```bash
for skill in devin-delegate kimi-delegate grok-delegate spark; do
  path="/home/agents/workspace/delegate-skill/skills/$skill"
  if [ -L "$path" ] && [ -e "$path" ]; then
    echo "OK: $skill -> $(readlink -f $path)"
  else
    echo "MISSING or BROKEN: $skill"
  fi
done
```

Expected: All four print `OK:` with resolved paths.

- [ ] **Step 3: Commit**

```bash
cd /home/agents/workspace/delegate-skill
git add skills/
git commit -m "feat(index): add skills/ symlinks for all four delegates [Agent: Claude Sonnet 4.6]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Write setup.sh for the index repo

**Files:**
- Create: `delegate-skill/setup.sh`

- [ ] **Step 1: Create setup.sh**

Create `delegate-skill/setup.sh`:

```bash
#!/usr/bin/env bash
# One-shot installer for all four AI delegation skills.
set -euo pipefail

DELEGATE_SKILL_ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$DELEGATE_SKILL_ROOT/skills"
mkdir -p "$SKILLS_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC}  $*"; }
fail() { echo -e "${RED}✗${NC} $*"; }

clone_or_skip() {
  local name="$1" url="$2" dest="$3"
  if [ -d "$dest/.git" ]; then
    ok "$name already installed at $dest"
  elif [ -n "$url" ]; then
    echo "Cloning $name from $url..."
    git clone "$url" "$dest"
    ok "Cloned $name"
  else
    warn "$name has no public remote. Skipping clone."
    return 1
  fi
}

run_skill_setup() {
  local name="$1" dir="$2"
  if [ -f "$dir/setup.sh" ]; then
    echo "Running $name/setup.sh..."
    bash "$dir/setup.sh" && ok "$name setup complete" || warn "$name setup exited with errors"
  else
    warn "$name has no setup.sh — skipping binary install"
  fi
}

link_skill() {
  local name="$1" target="$2"
  if [ -d "$target" ]; then
    ln -sfn "$target" "$SKILLS_DIR/$name"
    ok "Linked skills/$name -> $target"
  else
    warn "Cannot link $name: $target does not exist"
  fi
}

echo "=== delegate-skill installer ==="
echo ""

# --- devin-delegate ---
DEVIN_DEST="$HOME/.agents/skills/devin-delegate"
clone_or_skip "devin-delegate" "https://github.com/chimera-defi/devin-delegate.git" "$DEVIN_DEST" && \
  run_skill_setup "devin-delegate" "$DEVIN_DEST"
link_skill "devin-delegate" "$DEVIN_DEST"

# --- kimi-delegate ---
KIMI_DEST="$HOME/.agents/skills/kimi-delegate"
clone_or_skip "kimi-delegate" "https://github.com/chimera-defi/kimi-delegate-skill.git" "$KIMI_DEST" && \
  run_skill_setup "kimi-delegate" "$KIMI_DEST"
link_skill "kimi-delegate" "$KIMI_DEST"

# --- grok-delegate ---
GROK_DEST="$HOME/.agents/skills/grok-delegate"
GROK_URL=""  # No public remote yet; update when published.
GROK_LOCAL="${WORKSPACE:-$HOME/workspace}/grok-delegate"
if [ -d "$GROK_LOCAL/.git" ]; then
  echo "grok-delegate found locally at $GROK_LOCAL, linking..."
  ln -sfn "$GROK_LOCAL" "$GROK_DEST"
  ok "grok-delegate linked from local workspace"
else
  warn "grok-delegate not found locally and has no public remote — skipping."
fi
if [ -d "$GROK_DEST" ]; then
  run_skill_setup "grok-delegate" "$GROK_DEST"
  link_skill "grok-delegate" "$GROK_DEST"
fi

# --- spark (via gstack) ---
SPARK_PATH="$HOME/.claude/skills/gstack/spark"
if [ -d "$SPARK_PATH" ]; then
  link_skill "spark" "$SPARK_PATH"
else
  warn "spark not found at $SPARK_PATH — install gstack first: https://github.com/chimera-defi/gstack"
fi

echo ""
echo "=== Health checks ==="

check_cmd() {
  local name="$1" cmd="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    ok "$name binary: $(command -v "$cmd")"
  else
    fail "$name binary not found (run $name setup.sh manually)"
  fi
}

check_cmd "devin-delegate" "devin-delegate"
check_cmd "kimi-delegate" "kimi-delegate"
check_cmd "grok-delegate" "grok-delegate"

echo ""
echo "=== Routing summary ==="
cat <<'ROUTING'
  Browser / UI / screenshot        → devin-delegate
  Cheap research / review / draft  → kimi-delegate
  Multi-file refactor / large repo → grok-delegate
  Local Codex write-mode impl      → /spark (Claude Code skill)
  Unknown / orchestration          → kimi-delegate to scope, then escalate
ROUTING

echo ""
ok "delegate-skill installation complete."
```

```bash
chmod +x /home/agents/workspace/delegate-skill/setup.sh
```

- [ ] **Step 2: Dry-run setup.sh (everything should already be installed)**

```bash
cd /home/agents/workspace/delegate-skill
bash setup.sh 2>&1 | grep -E "✓|⚠|✗|===" | head -20
```

Expected: All four skills show `✓` lines (already installed). No `✗` lines.

- [ ] **Step 3: Commit**

```bash
cd /home/agents/workspace/delegate-skill
git add setup.sh
git commit -m "feat(index): add one-shot setup.sh installer [Agent: Claude Sonnet 4.6]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 8: Update CLAUDE.md and create AGENTS.md

**Files:**
- Modify: `delegate-skill/CLAUDE.md`
- Create: `delegate-skill/AGENTS.md`

- [ ] **Step 1: Rewrite CLAUDE.md with routing block**

Replace the contents of `delegate-skill/CLAUDE.md` with:

```markdown
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

| Task type | Delegate | Command |
|-----------|----------|---------|
| Browser, UI, screenshot, sandbox implementation | `devin-delegate` | `devin-delegate --task "..." --workspace /path/to/repo` |
| Cheap search / summarize / draft / review | `kimi-delegate` | `kimi-delegate --task "..."` |
| Multi-file refactor, large-codebase implementation | `grok-delegate` | `./skills/grok-delegate/scripts/delegate.py --task "..."` |
| Local Codex write-mode implementation | `spark` | `/spark` (Claude Code skill) |
| Unknown / orchestration | `kimi-delegate` first, then escalate | `kimi-delegate --task "scope: ..."` |

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
```

- [ ] **Step 2: Create AGENTS.md with the same routing block**

Create `delegate-skill/AGENTS.md`:

```markdown
# delegate-skill — Agent Routing (Codex / OpenAI / ChatGPT)

> This file provides routing guidance for non-Claude agents. For Claude Code, see CLAUDE.md.

<!-- delegate-skill:begin -->
## AI Delegation Routing

| Task type | Delegate | Command |
|-----------|----------|---------|
| Browser, UI, screenshot, sandbox implementation | `devin-delegate` | `devin-delegate --task "..." --workspace /path/to/repo` |
| Cheap search / summarize / draft / review | `kimi-delegate` | `kimi-delegate --task "..."` |
| Multi-file refactor, large-codebase implementation | `grok-delegate` | `./skills/grok-delegate/scripts/delegate.py --task "..."` |
| Local Codex write-mode implementation | `spark` | invoke via Codex write-mode |
| Unknown / orchestration | `kimi-delegate` first, then escalate | `kimi-delegate --task "scope: ..."` |

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
```

- [ ] **Step 3: Verify the routing blocks are present in both files**

```bash
grep -c "delegate-skill:begin" /home/agents/workspace/delegate-skill/CLAUDE.md
grep -c "delegate-skill:begin" /home/agents/workspace/delegate-skill/AGENTS.md
```

Expected: Both print `1`.

- [ ] **Step 4: Commit**

```bash
cd /home/agents/workspace/delegate-skill
git add CLAUDE.md AGENTS.md
git commit -m "feat(routing): add delegate routing blocks to CLAUDE.md and AGENTS.md [Agent: Claude Sonnet 4.6]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 9: Create GEMINI.md and README.md

**Files:**
- Create: `delegate-skill/GEMINI.md`
- Create: `delegate-skill/README.md`

- [ ] **Step 1: Create GEMINI.md**

Create `delegate-skill/GEMINI.md`:

```markdown
# delegate-skill — Gemini Agent Routing

> Gemini CLI agent: see AGENTS.md for the full delegation routing table and rules.
> The `<!-- delegate-skill:begin -->` block in AGENTS.md contains everything you need.

Run `bash setup.sh` to install all four delegate skills on a new machine.
```

- [ ] **Step 2: Create README.md**

Create `delegate-skill/README.md`:

```markdown
# delegate-skill

One-stop index for AI delegation skills. Install all four with a single command.

## Install

```bash
git clone https://github.com/chimera-defi/delegate-skill
cd delegate-skill
bash setup.sh
```

## Skills

| Skill | Purpose | Source |
|-------|---------|--------|
| `devin-delegate` | Browser, UI, screenshot, sandbox implementation | [chimera-defi/devin-delegate](https://github.com/chimera-defi/devin-delegate) |
| `kimi-delegate` | Cheap bounded research, summarize, draft, review | [chimera-defi/kimi-delegate-skill](https://github.com/chimera-defi/kimi-delegate-skill) |
| `grok-delegate` | Multi-file refactor, large-codebase implementation | local (no public remote yet) |
| `spark` | Local Codex write-mode implementation | via [gstack](https://github.com/chimera-defi/gstack) |

## Routing

| Task | Use |
|------|-----|
| Browser / UI / screenshot | `devin-delegate` |
| Search / summarize / review | `kimi-delegate` |
| Multi-file refactor / large repo | `grok-delegate` |
| Local Codex write-mode | `/spark` |
| Unclear scope | `kimi-delegate` to scope, then escalate |

Never call delegates directly (`opencode`, `devin`, `pi --provider kimi-coding`). Always use the wrapper binaries — they provide envelope, fallback, and telemetry.

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
```

- [ ] **Step 3: Commit**

```bash
cd /home/agents/workspace/delegate-skill
git add GEMINI.md README.md
git commit -m "feat(docs): add GEMINI.md stub and README [Agent: Claude Sonnet 4.6]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 10: Final verification

- [ ] **Step 1: Run setup.sh end-to-end**

```bash
cd /home/agents/workspace/delegate-skill
bash setup.sh
```

Expected: All four skills show `✓`. No `✗` lines.

- [ ] **Step 2: Verify skills/ symlinks resolve**

```bash
for skill in devin-delegate kimi-delegate grok-delegate spark; do
  path="/home/agents/workspace/delegate-skill/skills/$skill"
  if [ -L "$path" ] && [ -e "$path" ]; then
    echo "OK: $skill"
  else
    echo "FAIL: $skill"
  fi
done
```

Expected: All four print `OK:`.

- [ ] **Step 3: Verify .claude-plugin/plugin.json is valid JSON**

```bash
python3 -c "import json; json.load(open('.claude-plugin/plugin.json')); print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Verify routing blocks are present**

```bash
grep -l "delegate-skill:begin" CLAUDE.md AGENTS.md
```

Expected: Both files listed.

- [ ] **Step 5: Run delegate health checks**

```bash
devin-delegate --check 2>&1 | grep -i "all_ok"
kimi-delegate --check 2>&1 | grep -i "all_ok"
grok-delegate --check 2>&1 | grep -i "all_ok"
```

Expected: Each prints a line containing `"all_ok": true`.

- [ ] **Step 6: Verify grok-delegate SKILL.md has triggers**

```bash
python3 -c "
import re
text = open('skills/grok-delegate/SKILL.md').read()
m = re.match(r'^---\n(.+?)\n---', text, re.DOTALL)
import yaml
data = yaml.safe_load(m.group(1))
assert 'triggers' in data
print('OK: triggers =', data['triggers'])
"
```

Expected: `OK: triggers = ['delegate to Grok', ...]`
