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
