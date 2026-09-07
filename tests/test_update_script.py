from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_claude(path: Path, zone_b: str, zone_c: str) -> None:
    path.write_text(
        "\n".join(
            [
                "# CLAUDE.md",
                "<!-- ZONE_A_BEGIN -->",
                "zone a",
                "<!-- ZONE_A_END -->",
                "<!-- ZONE_B_BEGIN -->",
                zone_b,
                "<!-- ZONE_B_END -->",
                "<!-- ZONE_C_BEGIN -->",
                zone_c,
                "<!-- ZONE_C_END -->",
            ]
        ),
        encoding="utf-8",
    )


def test_update_preserves_user_state_and_removes_legacy_paths(tmp_path: Path) -> None:
    current = tmp_path / "current"
    source = tmp_path / "source"
    (current / "scripts").mkdir(parents=True)
    (source / "scripts").mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "update.sh", current / "scripts" / "update.sh")
    shutil.copy(ROOT / "scripts" / "update.sh", source / "scripts" / "update.sh")

    for root in [current, source]:
        (root / ".claude" / "hooks").mkdir(parents=True)
        (root / ".claude" / "agents").mkdir(parents=True)
        (root / ".claude" / "skills").mkdir(parents=True)

    write_claude(current / "CLAUDE.md", "project: keep", "phase: keep")
    write_claude(source / "CLAUDE.md", "project: template", "phase: template")
    (source / "AGENTS.md").write_text("template agents\n", encoding="utf-8")
    (source / ".claude" / "hooks" / "keep.py").write_text("print('ok')\n", encoding="utf-8")

    (current / ".claude" / "logs").mkdir(parents=True)
    (current / ".claude" / "logs" / "old.log").write_text("log\n", encoding="utf-8")
    (current / ".claude" / "tasks" / "task-1").mkdir(parents=True)
    (current / ".claude" / "tasks" / "task-1" / "state.json").write_text(
        "{}\n", encoding="utf-8"
    )
    for user_dir in ["docs", "src", "data", "notebooks", "tests"]:
        (current / user_dir).mkdir()
        (current / user_dir / "keep.txt").write_text("keep\n", encoding="utf-8")

    (current / "scripts" / "project_owned.py").write_text("mine\n", encoding="utf-8")
    (current / ".claude" / "tmp").mkdir()
    (current / ".claude" / "tmp" / "scratch.pdf").write_text("pdf\n", encoding="utf-8")
    (current / ".claude" / "settings.local.json").write_text("{\"local\": 1}", encoding="utf-8")
    (source / ".claude" / "settings.local.json").write_text("{\"template\": 1}", encoding="utf-8")
    (current / ".codex" / "plans").mkdir(parents=True)
    (current / ".codex" / "plans" / "plan.md").write_text("plan\n", encoding="utf-8")
    (current / ".gemini").mkdir()
    (current / ".gemini" / "GEMINI.md").write_text("old\n", encoding="utf-8")
    (current / ".claude" / "hooks" / "agent-router.py").write_text("old\n", encoding="utf-8")
    (current / ".claude" / "routing-keywords.json").write_text("{}", encoding="utf-8")

    subprocess.run(
        ["bash", "scripts/update.sh", "--source", str(source)],
        cwd=current,
        check=True,
        capture_output=True,
        text=True,
    )

    claude = (current / "CLAUDE.md").read_text(encoding="utf-8")
    assert "project: keep" in claude
    assert "phase: keep" in claude
    assert (current / ".claude" / "logs" / "old.log").exists()
    assert (current / ".claude" / "tasks" / "task-1" / "state.json").exists()
    assert (current / "docs" / "keep.txt").exists()
    assert (current / "scripts" / "project_owned.py").exists()
    assert (current / ".claude" / "tmp" / "scratch.pdf").exists()
    local_settings = (current / ".claude" / "settings.local.json").read_text(encoding="utf-8")
    assert local_settings == '{"local": 1}'
    assert (current / ".codex" / "plans" / "plan.md").exists()
    assert not (current / ".gemini").exists()
    assert not (current / ".claude" / "hooks" / "agent-router.py").exists()
    assert not (current / ".claude" / "routing-keywords.json").exists()
