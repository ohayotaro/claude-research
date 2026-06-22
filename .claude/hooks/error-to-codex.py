#!/usr/bin/env python3
"""Suggest the canonical Codex debug path after Python execution failures.

The hook does not launch Codex. It nudges the Research Lead to create a task
brief under `.claude/tasks/<task-id>/brief.md` and run:

    python scripts/codex_research.py debug <task-id> --prompt-file <brief>
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

PY_TB = re.compile(r"Traceback \(most recent call last\):", re.MULTILINE)
RUNNER_RE = re.compile(r"\b(uv\s+run\s+python|python3?|pytest)\b")


def _get_text_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def main() -> int:
    raw = sys.stdin.read() or "{}"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    inp = _get_text_mapping(payload.get("tool_input", {}))
    cmd = inp.get("command", "")
    if not isinstance(cmd, str):
        return 0
    response = _get_text_mapping(payload.get("tool_response", {}))
    stderr = response.get("stderr", "") or ""
    stdout = response.get("stdout", "") or ""
    exit_code = response.get("exit_code")
    phase = payload.get("hook_event_name", "")
    if not isinstance(stderr, str) or not isinstance(stdout, str):
        return 0

    is_failure = phase == "PostToolUseFailure" or (
        exit_code not in (0, None)
    )
    if not is_failure:
        return 0
    if not RUNNER_RE.search(cmd):
        return 0

    combined = stderr + "\n" + stdout
    if not PY_TB.search(combined):
        return 0

    last_lines = "\n".join(combined.strip().splitlines()[-6:])
    print(
        "[error-to-codex] Python 実行が失敗しました。"
        "Codex debug task を作成し、"
        "`python scripts/codex_research.py debug <task-id> --prompt-file "
        ".claude/tasks/<task-id>/brief.md` で解析することを推奨します。\n"
        f"末尾抜粋:\n{last_lines}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
