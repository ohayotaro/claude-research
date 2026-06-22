#!/usr/bin/env bash
# Update the claude-research template layer while preserving user project state.
#
# Preserved:
#   - CLAUDE.md Zone B and Zone C
#   - .claude/logs/** and .claude/tasks/**
#   - docs/**, src/**, data/**, notebooks/**, tests/**
#   - project-owned pyproject.toml, README.md, .gitignore, uv.lock
#
# Usage: bash scripts/update.sh --source <path-to-fresh-template-checkout>

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
warn() { printf "\033[33m[warn]\033[0m %s\n" "$*"; }
ok()   { printf "\033[32m[ok]\033[0m %s\n" "$*"; }
err()  { printf "\033[31m[err]\033[0m %s\n" "$*" >&2; }

SOURCE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --source) SOURCE="$2"; shift 2 ;;
        *) err "unknown arg: $1"; exit 2 ;;
    esac
done

if [[ -z "$SOURCE" ]]; then
    err "Pass --source <path-to-fresh-template-checkout>"
    exit 2
fi
if [[ ! -d "$SOURCE/.claude" || ! -f "$SOURCE/CLAUDE.md" ]]; then
    err "$SOURCE does not look like a claude-research checkout."
    exit 2
fi

for cmd in rsync python3 cmp; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        err "$cmd not found on PATH. Install it before running update.sh."
        exit 2
    fi
done

SRC_SCRIPT="$SOURCE/scripts/update.sh"
THIS_SCRIPT="${BASH_SOURCE[0]}"
if [[ -f "$SRC_SCRIPT" ]] && ! cmp -s "$SRC_SCRIPT" "$THIS_SCRIPT"; then
    bold "Self-bootstrap: source has a newer update.sh; replacing local copy and re-executing"
    TMP_SCRIPT="$(mktemp "${THIS_SCRIPT}.new.XXXXXX")"
    cp "$SRC_SCRIPT" "$TMP_SCRIPT"
    chmod +x "$TMP_SCRIPT"
    mv "$TMP_SCRIPT" "$THIS_SCRIPT"
    ok "scripts/update.sh updated from $SRC_SCRIPT"
    echo
    exec bash "$THIS_SCRIPT" --source "$SOURCE"
fi

BACKUP_DIR=".update-backup-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"

ROLLBACK_NEEDED=0
rollback() {
    local rc=$?
    if [[ "$ROLLBACK_NEEDED" == "1" && -f "$BACKUP_DIR/CLAUDE.md.before" ]]; then
        warn "update failed (exit $rc). Restoring CLAUDE.md from backup."
        cp "$BACKUP_DIR/CLAUDE.md.before" CLAUDE.md
        warn "Some template files may already have been partially overlaid."
        warn "Inspect $BACKUP_DIR and rerun after fixing the cause."
    fi
    exit "$rc"
}
trap rollback ERR

bold "Backing up Zone B, Zone C, root AGENTS.md, and CLAUDE.md"
cp CLAUDE.md "$BACKUP_DIR/CLAUDE.md.before"
if [[ -f AGENTS.md ]]; then
    cp AGENTS.md "$BACKUP_DIR/AGENTS.md.before"
fi
python3 - "$BACKUP_DIR" <<'PY'
import pathlib
import re
import sys

backup = pathlib.Path(sys.argv[1])
text = pathlib.Path("CLAUDE.md").read_text(encoding="utf-8")
for zone in ("B", "C"):
    match = re.search(
        rf"<!-- ZONE_{zone}_BEGIN -->(.*?)<!-- ZONE_{zone}_END -->",
        text,
        re.DOTALL,
    )
    if not match and zone == "B":
        raise SystemExit("ZONE_B markers not found in current CLAUDE.md")
    if match:
        (backup / f"ZONE_{zone}.md").write_text(match.group(1), encoding="utf-8")
PY
if [[ ! -s "$BACKUP_DIR/ZONE_B.md" ]]; then
    err "Zone B backup is empty or missing."
    exit 3
fi
ok "Saved Zone B to $BACKUP_DIR/ZONE_B.md"
if [[ -s "$BACKUP_DIR/ZONE_C.md" ]]; then
    ok "Saved Zone C to $BACKUP_DIR/ZONE_C.md"
else
    warn "Zone C not backed up; template default will remain."
fi

python3 - "$SOURCE" <<'PY'
import pathlib
import sys

text = (pathlib.Path(sys.argv[1]) / "CLAUDE.md").read_text(encoding="utf-8")
required = [
    "<!-- ZONE_B_BEGIN -->",
    "<!-- ZONE_B_END -->",
    "<!-- ZONE_C_BEGIN -->",
    "<!-- ZONE_C_END -->",
]
missing = [marker for marker in required if marker not in text]
if missing:
    raise SystemExit(f"template CLAUDE.md is missing markers {missing}")
PY

ROLLBACK_NEEDED=1

bold "Overlaying template from $SOURCE"
if [[ -d "$SOURCE/.claude" ]]; then
    rsync -a --delete \
        --exclude='logs/' \
        --exclude='logs/**' \
        --exclude='tasks/' \
        --exclude='tasks/**' \
        "$SOURCE/.claude/" ".claude/"
    ok "synced .claude/"
fi

if [[ -d "$SOURCE/scripts" ]]; then
    rsync -a --delete "$SOURCE/scripts/" "scripts/"
    ok "synced scripts/"
fi

cp "$SOURCE/CLAUDE.md" CLAUDE.md
ok "replaced CLAUDE.md (Zone B and Zone C will be restored)"

if [[ -f "$SOURCE/AGENTS.md" ]]; then
    cp "$SOURCE/AGENTS.md" AGENTS.md
    ok "synced AGENTS.md"
elif [[ -f "$BACKUP_DIR/AGENTS.md.before" ]]; then
    warn "source has no AGENTS.md; preserving existing root AGENTS.md"
    cp "$BACKUP_DIR/AGENTS.md.before" AGENTS.md
fi

bold "Removing known obsolete template paths"
for path in \
    .gemini \
    .codex \
    .claude/skills/ask-gemini \
    .claude/agents/gemini-explore.md \
    .claude/agents/literature-reviewer.md \
    .claude/agents/hypothesis-generator.md \
    .claude/agents/methodology-designer.md \
    .claude/agents/experiment-runner.md \
    .claude/agents/data-analyst.md \
    .claude/agents/discussant.md \
    .claude/agents/paper-writer.md \
    .claude/agents/peer-reviewer.md \
    .claude/agents/script-reviewer.md \
    .claude/agents/viz-reviewer.md \
    .claude/agents/codex-debugger.md \
    .claude/routing-keywords.json \
    .claude/hooks/agent-router.py \
    .claude/hooks/research-keyword-detector.py \
    .claude/hooks/log-cli-tools.py \
    .claude/rules/agent-routing.md
do
    if [[ -e "$path" ]]; then
        rm -rf "$path"
        ok "removed $path"
    fi
done

bold "Restoring Zone B and Zone C"
python3 - "$BACKUP_DIR" <<'PY'
import pathlib
import re
import sys

backup = pathlib.Path(sys.argv[1])
zone_b = (backup / "ZONE_B.md").read_text(encoding="utf-8")
zone_c_path = backup / "ZONE_C.md"
zone_c = zone_c_path.read_text(encoding="utf-8") if zone_c_path.exists() else None

text = pathlib.Path("CLAUDE.md").read_text(encoding="utf-8")
for marker in (
    "<!-- ZONE_B_BEGIN -->",
    "<!-- ZONE_B_END -->",
    "<!-- ZONE_C_BEGIN -->",
    "<!-- ZONE_C_END -->",
):
    if marker not in text:
        raise SystemExit(f"post-overlay CLAUDE.md missing {marker}")

text = re.sub(
    r"(<!-- ZONE_B_BEGIN -->).*?(<!-- ZONE_B_END -->)",
    lambda match: match.group(1) + zone_b + match.group(2),
    text,
    count=1,
    flags=re.DOTALL,
)
if zone_c is not None:
    text = re.sub(
        r"(<!-- ZONE_C_BEGIN -->).*?(<!-- ZONE_C_END -->)",
        lambda match: match.group(1) + zone_c + match.group(2),
        text,
        count=1,
        flags=re.DOTALL,
    )
pathlib.Path("CLAUDE.md").write_text(text, encoding="utf-8")
PY
ok "Zone B restored from backup"
if [[ -s "$BACKUP_DIR/ZONE_C.md" ]]; then
    ok "Zone C restored from backup"
fi

ROLLBACK_NEEDED=0
trap - ERR

echo
ok "Update complete."
echo "  Backup: $BACKUP_DIR/"
echo "  Restart Claude Code so updated skills, hooks, and agents are loaded."
