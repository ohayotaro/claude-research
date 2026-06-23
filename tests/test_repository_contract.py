from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def active_files() -> list[Path]:
    ignored_parts = {".git", ".venv", "logs", "tasks", "__pycache__"}
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in ignored_parts for part in rel.parts):
            continue
        if path.suffix == ".tmp":
            continue
        files.append(path)
    return files


def test_single_project_subagent() -> None:
    agents = sorted((ROOT / ".claude" / "agents").glob("*.md"))
    assert [agent.name for agent in agents] == ["scientific-author.md"]


def test_no_legacy_active_paths() -> None:
    assert not (ROOT / ".gemini").exists()
    assert not (ROOT / ".codex" / "AGENTS.md").exists()
    assert not (ROOT / ".claude" / "routing-keywords.json").exists()
    assert not (ROOT / ".claude" / "hooks" / "agent-router.py").exists()
    assert not (ROOT / ".claude" / "hooks" / "research-keyword-detector.py").exists()
    assert not (ROOT / ".claude" / "rules" / "agent-routing.md").exists()


def test_no_delegated_agent_metadata() -> None:
    for path in (ROOT / ".claude" / "skills").rglob("SKILL.md"):
        assert "delegated_agent:" not in path.read_text(encoding="utf-8")


def test_root_agents_contract_exists() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Builder mode" in agents
    assert "Reviewer mode" in agents
    assert "read-only" in agents


def test_no_active_legacy_invocation_references() -> None:
    allowed_cleanup_file = ROOT / "scripts" / "update.sh"
    prefix = "ge" + "mini"
    forbidden = [
        f"{prefix} CLI",
        f"{prefix} --version",
        "ask-" + prefix,
        prefix + "-explore",
    ]
    for path in active_files():
        if path == allowed_cleanup_file:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in forbidden:
            assert needle not in text, f"{needle!r} found in {path}"


def test_author_skills_use_explicit_agent_fork() -> None:
    expected = {
        "literature-review",
        "extend-literature",
        "paper-deep-read",
        "identify-gaps",
        "generate-hypothesis",
        "design-experiment",
        "discuss-results",
        "write-paper",
        "revise",
    }
    for name in expected:
        text = (ROOT / ".claude" / "skills" / name / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert "context: fork" in text
        assert "agent: scientific-author" in text
