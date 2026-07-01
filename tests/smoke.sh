#!/usr/bin/env bash
# Hermetic smoke test for delegate-skill/setup.sh.
#
# Runs setup.sh against a scratch HOME with stubbed delegate binaries and asserts:
#   * the global CLAUDE.md routing block is injected exactly once and stays
#     idempotent across repeated runs,
#   * the ~/.claude/skills/delegate-skill registration symlink is created,
#   * setup.sh reports all three delegate --check binaries resolve (via PATH stubs).
#
# No network and no real delegate installs: clone destinations are pre-stubbed as
# symlinks so clone_or_skip() takes its "already installed" branch.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRATCH="$(mktemp -d)"
cleanup() {
  rm -rf "$SCRATCH"
  # setup.sh writes gitignored skills/ symlinks into the repo; drop them so the
  # working tree stays clean after the test.
  rm -rf "$REPO_ROOT/skills"
}
trap cleanup EXIT

pass=0
fail=0
check() { # check "description" cmd...
  local desc="$1"; shift
  if "$@"; then
    echo "  PASS  $desc"; pass=$((pass + 1))
  else
    echo "  FAIL  $desc"; fail=$((fail + 1))
  fi
}

# --- Build a hermetic environment -------------------------------------------
export HOME="$SCRATCH/home"
mkdir -p "$HOME/.claude/skills"
: > "$HOME/.claude/CLAUDE.md"

# Stub delegate binaries on PATH so setup.sh's `command -v` checks resolve and no
# sub-skill setup.sh runs (keeps the test network-free).
BIN="$SCRATCH/bin"
mkdir -p "$BIN"
for d in devin-delegate kimi-delegate grok-delegate; do
  printf '#!/usr/bin/env bash\necho "%s stub ok"\n' "$d" > "$BIN/$d"
  chmod +x "$BIN/$d"
done
export PATH="$BIN:$PATH"

# Pre-stub clone destinations as symlinks to a real dir so clone_or_skip() skips
# `git clone` (its `[ -L ] && [ -d ]` branch returns "already installed").
mkdir -p "$SCRATCH/stubskill" "$HOME/.agents/skills"
for d in devin-delegate kimi-delegate grok-delegate; do
  ln -sfn "$SCRATCH/stubskill" "$HOME/.agents/skills/$d"
done

MARK_BEGIN="delegate-skill:begin"

# --- Run setup.sh twice (second run proves idempotency) ---------------------
bash "$REPO_ROOT/setup.sh" > "$SCRATCH/run1.log" 2>&1 || true
count1=$(grep -c "$MARK_BEGIN" "$HOME/.claude/CLAUDE.md" || true)

bash "$REPO_ROOT/setup.sh" > "$SCRATCH/run2.log" 2>&1 || true
count2=$(grep -c "$MARK_BEGIN" "$HOME/.claude/CLAUDE.md" || true)

echo "delegate-skill smoke test"
check "setup.sh is valid bash (bash -n)"        bash -n "$REPO_ROOT/setup.sh"
check "routing block injected on first run"     test "$count1" -eq 1
check "routing block idempotent on second run"  test "$count2" -eq 1
check "global skill symlink registered"         test -L "$HOME/.claude/skills/delegate-skill"
check "devin --check binary resolved"           grep -q "devin-delegate binary:" "$SCRATCH/run2.log"
check "kimi --check binary resolved"            grep -q "kimi-delegate binary:" "$SCRATCH/run2.log"
check "grok --check binary resolved"            grep -q "grok-delegate binary:" "$SCRATCH/run2.log"

echo ""
echo "passed=$pass failed=$fail"
test "$fail" -eq 0
