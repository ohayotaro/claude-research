#!/usr/bin/env bash
# Update the orchestrator template layer (.claude/, .codex/, .gemini/, scripts/)
# while preserving:
#   - Zone B of CLAUDE.md  (the user's project configuration)
#   - Zone C of CLAUDE.md  (the user's session progress / next-action state)
#   - .claude/logs/        (runtime logs from prior sessions)
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
if [[ ! -d "$SOURCE/.claude" ]]; then
    err "$SOURCE does not look like a claude-research-orchestrator checkout (no .claude/)."
    exit 2
fi
if [[ ! -f "$SOURCE/CLAUDE.md" ]]; then
    err "$SOURCE has no CLAUDE.md."
    exit 2
fi

# --- Required external commands -------------------------------------
for cmd in rsync python3 cmp; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        err "$cmd not found on PATH. Install it before running update.sh."
        exit 2
    fi
done

# --- Self-bootstrap --------------------------------------------------
# If the source ships a newer update.sh than what we are currently
# running, atomically swap it in and re-execute. Without this, a bug in
# the local update.sh can never be fixed via the update flow itself —
# the user would have to manually copy the fixed script first.
# Idempotent: when local matches source, this block is a no-op.
SRC_SCRIPT="$SOURCE/scripts/update.sh"
THIS_SCRIPT="${BASH_SOURCE[0]}"
if [[ -f "$SRC_SCRIPT" ]] && ! cmp -s "$SRC_SCRIPT" "$THIS_SCRIPT"; then
    bold "Self-bootstrap: source has a newer update.sh; replacing local copy and re-executing"
    TMP_SCRIPT="$(mktemp "${THIS_SCRIPT}.new.XXXXXX")"
    cp "$SRC_SCRIPT" "$TMP_SCRIPT"
    chmod +x "$TMP_SCRIPT"
    mv "$TMP_SCRIPT" "$THIS_SCRIPT"
    ok "scripts/update.sh updated from $SRC_SCRIPT (atomic mv)"
    echo
    exec bash "$THIS_SCRIPT" --source "$SOURCE"
fi

# Backup directory MUST live outside any rsync target. We use the repo root
# with a clearly-named timestamped directory; .gitignore excludes it.
BACKUP_DIR=".update-backup-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"

# --- Transactional rollback -----------------------------------------
# If anything below the backup step fails, restore CLAUDE.md from the
# backup so the user is never left with the template's placeholder Zone
# B / C in their CLAUDE.md.
ROLLBACK_NEEDED=0
rollback() {
    local rc=$?
    if [[ "$ROLLBACK_NEEDED" == "1" && -f "$BACKUP_DIR/CLAUDE.md.before" ]]; then
        warn "update failed (exit $rc). Restoring CLAUDE.md from backup."
        cp "$BACKUP_DIR/CLAUDE.md.before" CLAUDE.md
        warn "CLAUDE.md restored. Note that .claude/ / .codex/ / .gemini/ /"
        warn "scripts/ may already have been partially overlaid — inspect"
        warn "$BACKUP_DIR for the pre-update state and rerun once the cause"
        warn "is fixed."
    fi
    exit "$rc"
}
trap rollback ERR

# --- Extract Zone B and Zone C from the current CLAUDE.md ------------
bold "Backing up Zone B (project config), Zone C (session state), and CLAUDE.md"
cp CLAUDE.md "$BACKUP_DIR/CLAUDE.md.before"
python3 - "$BACKUP_DIR" <<'PY'
import re, sys, pathlib
backup = pathlib.Path(sys.argv[1])
src = pathlib.Path("CLAUDE.md").read_text(encoding="utf-8")

mb = re.search(r"<!-- ZONE_B_BEGIN -->(.*?)<!-- ZONE_B_END -->", src, re.DOTALL)
if not mb:
    raise SystemExit("ZONE_B markers not found in current CLAUDE.md")
(backup / "ZONE_B.md").write_text(mb.group(1), encoding="utf-8")

mc = re.search(r"<!-- ZONE_C_BEGIN -->(.*?)<!-- ZONE_C_END -->", src, re.DOTALL)
# Zone C may be absent in very old templates; warn but do not fail.
if mc:
    (backup / "ZONE_C.md").write_text(mc.group(1), encoding="utf-8")
else:
    print("warn: ZONE_C markers not found in current CLAUDE.md; skipping Zone C backup")
PY
if [[ ! -s "$BACKUP_DIR/ZONE_B.md" ]]; then
    err "Zone B backup is empty or missing — aborting before any destructive sync."
    exit 3
fi
ok "Saved Zone B to $BACKUP_DIR/ZONE_B.md"
if [[ -s "$BACKUP_DIR/ZONE_C.md" ]]; then
    ok "Saved Zone C to $BACKUP_DIR/ZONE_C.md"
else
    warn "Zone C not backed up (markers missing in current CLAUDE.md)."
fi

# --- Verify the source CLAUDE.md has the markers we will restore into
python3 - "$SOURCE" <<'PY'
import re, sys, pathlib
src = pathlib.Path(sys.argv[1]) / "CLAUDE.md"
text = src.read_text(encoding="utf-8")
required = ["<!-- ZONE_B_BEGIN -->", "<!-- ZONE_B_END -->",
            "<!-- ZONE_C_BEGIN -->", "<!-- ZONE_C_END -->"]
missing = [m for m in required if m not in text]
if missing:
    raise SystemExit(f"template CLAUDE.md is missing markers {missing}; refusing to overlay")
PY

# From this point on, a failure must trigger CLAUDE.md restoration.
ROLLBACK_NEEDED=1

# --- Overlay template ------------------------------------------------
bold "Overlaying template from $SOURCE"
for d in .claude .codex .gemini scripts; do
    if [[ -d "$SOURCE/$d" ]]; then
        if [[ "$d" == ".claude" ]]; then
            # Preserve runtime logs that the template never ships.
            rsync -a --delete \
                --exclude='logs/' \
                --exclude='logs/**' \
                "$SOURCE/$d/" "./$d/"
        else
            rsync -a --delete "$SOURCE/$d/" "./$d/"
        fi
        ok "synced $d/"
    fi
done
cp "$SOURCE/CLAUDE.md" CLAUDE.md
ok "replaced CLAUDE.md (Zone B and Zone C will be restored)"

# --- Restore Zone B and Zone C ---------------------------------------
bold "Restoring Zone B and Zone C"
python3 - "$BACKUP_DIR" <<'PY'
import re, sys, pathlib
backup = pathlib.Path(sys.argv[1])

zb_path = backup / "ZONE_B.md"
if not zb_path.exists():
    raise SystemExit(f"backup file vanished: {zb_path}")
zb = zb_path.read_text(encoding="utf-8")

zc_path = backup / "ZONE_C.md"
zc = zc_path.read_text(encoding="utf-8") if zc_path.exists() else None

src = pathlib.Path("CLAUDE.md").read_text(encoding="utf-8")
for marker in ("<!-- ZONE_B_BEGIN -->", "<!-- ZONE_B_END -->",
               "<!-- ZONE_C_BEGIN -->", "<!-- ZONE_C_END -->"):
    if marker not in src:
        raise SystemExit(f"post-overlay CLAUDE.md is missing {marker}; refusing to write")

src = re.sub(
    r"(<!-- ZONE_B_BEGIN -->).*?(<!-- ZONE_B_END -->)",
    lambda m: m.group(1) + zb + m.group(2),
    src, count=1, flags=re.DOTALL,
)
if zc is not None:
    src = re.sub(
        r"(<!-- ZONE_C_BEGIN -->).*?(<!-- ZONE_C_END -->)",
        lambda m: m.group(1) + zc + m.group(2),
        src, count=1, flags=re.DOTALL,
    )
pathlib.Path("CLAUDE.md").write_text(src, encoding="utf-8")
PY
ok "Zone B restored from backup"
if [[ -s "$BACKUP_DIR/ZONE_C.md" ]]; then
    ok "Zone C restored from backup"
else
    warn "Zone C left at template default (no backup was available)."
fi

# Reached the end successfully — disable the rollback trap.
ROLLBACK_NEEDED=0
trap - ERR

echo
ok "Update complete."
echo "  Backup: $BACKUP_DIR/  (safe to delete once you have verified the update)"
echo "  Tip: diff your CLAUDE.md against $BACKUP_DIR/CLAUDE.md.before to review."
