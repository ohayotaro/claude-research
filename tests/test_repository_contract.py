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


def _frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    return text.split("---", 2)[1]


def test_no_skill_mixes_author_fork_with_codex_runner() -> None:
    for path in (ROOT / ".claude" / "skills").rglob("SKILL.md"):
        text = path.read_text(encoding="utf-8")
        fm = _frontmatter(text)
        mixes_author_fork = "context: fork" in fm and "agent: scientific-author" in fm
        assert not (
            mixes_author_fork and "codex_research.py" in text
        ), f"author fork mixes Codex runner in {path}"


def test_multi_phase_skills_have_explicit_invocations() -> None:
    required = {
        "generate-hypothesis": [
            "PM-orchestrated multi-phase",
            "scientific-author",
            "hypothesis-writing",
            "python scripts/codex_research.py review",
            "Zone C",
        ],
        "design-experiment": [
            "PM-orchestrated multi-phase",
            "scientific-author",
            "methodology-writing",
            "python scripts/codex_research.py review",
            "Zone C",
        ],
        "prepare-submission": [
            "PM-orchestrated multi-phase",
            "python scripts/codex_research.py build",
            "submission-prose",
            "submitted",
        ],
        "release-artifacts": [
            "PM-orchestrated multi-phase",
            "python scripts/codex_research.py build",
            "release-prose",
            "final explicit user approval",
            "Zone C",
        ],
    }
    for name, markers in required.items():
        text = (ROOT / ".claude" / "skills" / name / "SKILL.md").read_text(
            encoding="utf-8"
        )
        for marker in markers:
            assert marker in text, f"{marker!r} missing from {name}"


def test_editorial_policy_markers_present() -> None:
    required = {
        ".claude/rules/writing-style.md": [
            "## Artifact purposes",
            "## Placement of content and caveats",
            "## Terminology",
        ],
        ".claude/rules/research-integrity.md": [
            "never by whether a result is favorable",
        ],
        ".claude/agents/scientific-author.md": [
            "## Editorial Brief",
            "## Revision Operations",
            "consolidation",
            "relocation",
        ],
        ".claude/skills/write-paper/SKILL.md": ["editorial brief"],
        ".claude/skills/peer-review/SKILL.md": ["Editorial assessment"],
        ".claude/skills/revise/SKILL.md": ["consolidation", "relocation"],
        ".claude/skills/checkpoint/SKILL.md": ["`notes` is at most 4 lines", "stale:"],
        ".claude/rules/language.md": ["## Clarity"],
        "CLAUDE.md": ["### Communication"],
    }
    # Markers check structure only; readability is judged by review, not by tests.
    for rel, markers in required.items():
        text = " ".join((ROOT / rel).read_text(encoding="utf-8").split())
        for marker in markers:
            assert marker in text, f"{marker!r} missing from {rel}"
