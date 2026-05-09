#!/usr/bin/env bash
# Setup script for claude-research.
# Detects optional CLI partners (codex, gemini) and bootstraps the Python env.
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

# --- uv ---------------------------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
    err "uv not found. Install from https://github.com/astral-sh/uv and rerun."
    exit 1
fi
ok "uv: $(uv --version)"

# --- Python deps ------------------------------------------------------
bold "Syncing Python dependencies via uv"
uv sync --extra dev
ok "Python environment ready"

# --- Codex CLI (optional) --------------------------------------------
CODEX_AVAILABLE=0
if command -v codex >/dev/null 2>&1; then
    CODEX_AVAILABLE=1
    ok "codex CLI detected: $(codex --version 2>/dev/null || echo 'version unknown')"
else
    warn "codex CLI not found. Strict review / logical verification will fall back to Claude subagents."
    warn "  Install: https://github.com/openai/codex"
fi

# --- Gemini CLI (optional) -------------------------------------------
GEMINI_AVAILABLE=0
if command -v gemini >/dev/null 2>&1; then
    GEMINI_AVAILABLE=1
    ok "gemini CLI detected"
else
    warn "gemini CLI not found. Multimodal / web research will fall back to Claude subagents."
    warn "  Install: https://github.com/google-gemini/gemini-cli"
fi

# --- Claude Code CLI (required for the next step) --------------------
if command -v claude >/dev/null 2>&1; then
    ok "claude CLI detected"
else
    warn "claude CLI not found on PATH. The orchestrator runs inside Claude Code —"
    warn "  Install:        https://claude.com/code"
    warn "  After install:  run 'claude' in this directory to start a session."
fi

# --- Persist detection result ----------------------------------------
mkdir -p .claude/logs
cat > .claude/logs/setup-status.json <<EOF
{
  "codex_available": $([ "$CODEX_AVAILABLE" = "1" ] && echo true || echo false),
  "gemini_available": $([ "$GEMINI_AVAILABLE" = "1" ] && echo true || echo false),
  "uv_version": "$(uv --version | awk '{print $2}')",
  "checked_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
ok "Wrote .claude/logs/setup-status.json"

# --- Directory scaffold (only created lazily by /init-research) ------
echo
bold "Next steps"
echo "  1. Open this directory in Claude Code:    claude"
echo "  2. Inside Claude, run:                    /init-research"
echo
ok "Setup complete."
