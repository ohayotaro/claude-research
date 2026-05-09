#!/usr/bin/env python3
"""SessionStart hook. Read CLAUDE.md Zone B and Zone C and print a concise
status to the user (Japanese), so the orchestrator and the user start aligned.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def _project_root() -> Path:
    root = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(root).resolve() if root else Path.cwd().resolve()

ZONE_B = re.compile(r"<!-- ZONE_B_BEGIN -->(.*?)<!-- ZONE_B_END -->", re.DOTALL)
ZONE_C = re.compile(r"<!-- ZONE_C_BEGIN -->(.*?)<!-- ZONE_C_END -->", re.DOTALL)
KV_RE = re.compile(r"^\s*([a-zA-Z_][\w]*)\s*:\s*(.+?)\s*$", re.MULTILINE)


def parse_kv(block: str) -> dict[str, str]:
    out: dict[str, str] = {}
    in_yaml = False
    for line in block.splitlines():
        if line.strip().startswith("```"):
            in_yaml = not in_yaml
            continue
        if not in_yaml:
            continue
        m = KV_RE.match(line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def main() -> int:
    p = _project_root() / "CLAUDE.md"
    if not p.exists():
        return 0
    text = p.read_text(encoding="utf-8")
    zb = ZONE_B.search(text)
    zc = ZONE_C.search(text)
    b = parse_kv(zb.group(1)) if zb else {}
    c = parse_kv(zc.group(1)) if zc else {}

    status = b.get("status", "uninitialized")
    if status == "uninitialized":
        print(
            "[session-start] 研究プロジェクトは未初期化です。"
            "最初に `/init-research` を実行してください。"
        )
        return 0

    theme = b.get("theme", "(未設定)")
    rq = b.get("research_question", "(未設定)")
    phase = c.get("current_phase", "not_started")
    next_action = c.get("next_action", "(未設定)")
    last_run = c.get("last_run_id", "null")

    print(
        "[session-start] 研究プロジェクトを読み込みました。\n"
        f"  テーマ: {theme}\n"
        f"  RQ: {rq}\n"
        f"  現在のフェーズ: {phase}（最終 run_id: {last_run}）\n"
        f"  次のアクション: {next_action}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
