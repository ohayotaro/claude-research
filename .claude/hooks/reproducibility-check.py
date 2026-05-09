#!/usr/bin/env python3
"""PostToolUse hook on Write under data/results/.

When any file is written under data/results/<run_id>/, ensure the run directory
ends up with a valid metadata.json containing all required fields. If the run
is "finished" (i.e. files exist but metadata is missing or incomplete),
emit a strong warning to the user.

This is a guardrail; the experiment-runner agent should write metadata.json
*first*, but operators may write outputs by hand. We complain loudly when that
breaks the reproducibility contract.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REQUIRED_KEYS = {
    "run_id",
    "started_at",
    "script",
    "args",
    "seed",
    "git_rev",
    "python_version",
    "platform",
    "package_versions",
}


def _project_root() -> Path:
    root = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(root).resolve() if root else Path.cwd().resolve()


def _run_id_for(path: str) -> str | None:
    """If `path` is under <project>/data/results/<run_id>/, return run_id."""
    if not path:
        return None
    try:
        rel = Path(path).resolve().relative_to(_project_root())
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) < 3 or parts[0] != "data" or parts[1] != "results":
        return None
    return parts[2]


def main() -> int:
    raw = sys.stdin.read() or "{}"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    inp = payload.get("tool_input", {}) or {}
    path = inp.get("file_path", "")
    run_id = _run_id_for(path)
    if not run_id:
        return 0
    run_dir = _project_root() / "data" / "results" / run_id
    if not run_dir.exists():
        return 0  # nothing to check yet
    md_path = run_dir / "metadata.json"

    # Skip the check if we ARE writing metadata.json itself (it might be
    # incomplete mid-write; the runner should set finished_at later).
    if Path(path).name == "metadata.json":
        return 0

    if not md_path.exists():
        print(
            f"[reproducibility-check] {run_dir}/ に出力ファイルがあるにもかかわらず "
            "metadata.json が存在しません。experiment-runner は metadata.json を"
            f"最初に書く契約です。`{run_dir}` を一度クリアし、"
            "src/utils/repro.py の write_metadata を経由して再実行してください。"
        )
        return 0

    try:
        md = json.loads(md_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"[reproducibility-check] {md_path} の JSON parse に失敗しました。")
        return 0
    if not isinstance(md, dict):
        print(
            f"[reproducibility-check] {md_path} のトップレベルが JSON object では"
            "ありません。schema は .claude/rules/reproducibility.md を参照してください。"
        )
        return 0
    missing = REQUIRED_KEYS - md.keys()
    if missing:
        print(
            f"[reproducibility-check] 再現性メタが不足しています ({md_path}): "
            f"{', '.join(sorted(missing))} が欠落しています。"
            " src/utils/repro.write_metadata を使うと自動的に揃います。"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
