#!/usr/bin/env bash
# Setup script for claude-research.
# Detects Claude and Codex tooling and bootstraps the Python environment.
# Idempotent: safe to run multiple times.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
warn() { printf "\033[33m[warn]\033[0m %s\n" "$*"; }
ok()   { printf "\033[32m[ok]\033[0m %s\n" "$*"; }
err()  { printf "\033[31m[err]\033[0m %s\n" "$*" >&2; }

bold "claude-research setup"
echo

if ! command -v uv >/dev/null 2>&1; then
    err "uv not found. Install uv and rerun setup."
    exit 1
fi
ok "uv: $(uv --version)"

bold "Syncing Python dependencies via uv"
uv sync --extra dev
ok "Python environment ready"

CODEX_AVAILABLE=0
CODEX_VERSION="unavailable"
if command -v codex >/dev/null 2>&1; then
    CODEX_AVAILABLE=1
    CODEX_VERSION="$(codex --version 2>/dev/null || echo 'version unknown')"
    ok "codex CLI detected: $CODEX_VERSION"
else
    warn "codex CLI not found. Codex builder/reviewer tasks will be blocked until installed."
    warn "  Install: https://github.com/openai/codex"
fi

CLAUDE_AVAILABLE=0
CLAUDE_VERSION="unavailable"
if command -v claude >/dev/null 2>&1; then
    CLAUDE_AVAILABLE=1
    CLAUDE_VERSION="$(claude --version 2>/dev/null || echo 'version unknown')"
    ok "claude CLI detected: $CLAUDE_VERSION"
else
    warn "claude CLI not found on PATH. Install Claude Code, then run 'claude' here."
fi

mkdir -p .claude/logs
cat > .claude/logs/setup-status.json <<EOF
{
  "schema_version": "2.0",
  "codex_available": $([ "$CODEX_AVAILABLE" = "1" ] && echo true || echo false),
  "codex_version": "$CODEX_VERSION",
  "claude_available": $([ "$CLAUDE_AVAILABLE" = "1" ] && echo true || echo false),
  "claude_version": "$CLAUDE_VERSION",
  "uv_version": "$(uv --version | awk '{print $2}')",
  "checked_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
ok "Wrote .claude/logs/setup-status.json"

echo
bold "Next steps"
echo "  1. Open this directory in Claude Code:    claude"
echo "  2. Inside Claude, run:                    /init-research"
echo
ok "Setup complete."
