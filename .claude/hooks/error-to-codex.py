#!/usr/bin/env python3
"""PostToolUse + PostToolUseFailure hook on Bash. When a `python` / `pytest`
/ `uv run` command exits non-zero (or fails outright) with a recognizable
Python traceback, suggest delegating to codex-debugger.

We do not auto-launch the agent — only nudge. Auto-launch would surprise
users during routine debugging.

The hook payload schema we expect downstream codex-debugger to receive
(via the orchestrator) is:
  {run_id?, script_path, traceback, env, last_commit?}
We surface a structured snippet here; the orchestrator builds the rest.
"""

from __future__ import annotations

import json
import re
import sys

PY_TB = re.compile(r"Traceback \(most recent call last\):", re.MULTILINE)
RUNNER_RE = re.compile(r"\b(uv\s+run\s+python|python3?|pytest)\b")


def main() -> int:
    raw = sys.stdin.read() or "{}"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    inp = payload.get("tool_input", {}) or {}
    cmd = inp.get("command", "")
    response = payload.get("tool_response", {}) or {}
    stderr = response.get("stderr", "") or ""
    stdout = response.get("stdout", "") or ""
    exit_code = response.get("exit_code")
    phase = payload.get("hook_event_name", "")

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
        "`codex-debugger` に root-cause 解析を依頼することを推奨します。\n"
        f"末尾抜粋:\n{last_lines}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
