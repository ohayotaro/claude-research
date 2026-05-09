#!/usr/bin/env python3
"""SessionEnd hook. Append a one-line session summary to .claude/logs/sessions.log.

Does NOT modify Zone C — that is /checkpoint's job, run intentionally by the
orchestrator. We only persist a lightweight breadcrumb here so a human can
audit when each session ended.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def _project_root() -> Path:
    root = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(root).resolve() if root else Path.cwd().resolve()


def main() -> int:
    raw = sys.stdin.read() or "{}"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = {}
    reason = payload.get("reason", "unknown")
    ts = datetime.now(timezone.utc).isoformat()
    log = _project_root() / ".claude" / "logs" / "sessions.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(f"{ts} session_end reason={reason}\n")

    if reason == "logout":
        print(
            "[session-end] セッションを終了します。"
            "進捗の永続化が必要な場合は、次回開始前に `/checkpoint` を実行してください。"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
