from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_hook(name: str) -> ModuleType:
    path = ROOT / ".claude" / "hooks" / name
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_citation_guard_detects_uncited_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(ROOT))
    hook = load_hook("citation-guard.py")
    assert hook.is_doc_path(str(ROOT / "docs" / "research" / "analysis.md"))
    findings = hook.find_uncited_claims(
        "Prior work shows that this method improves accuracy in many benchmarks."
    )
    assert findings


def test_reproducibility_hook_run_id_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(ROOT))
    hook = load_hook("reproducibility-check.py")
    path = ROOT / "data" / "results" / "run-1" / "values.csv"
    assert hook._run_id_for(str(path)) == "run-1"
    assert hook._run_id_for(str(ROOT / "docs" / "x.md")) is None


def test_error_to_codex_mentions_canonical_runner() -> None:
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_input": {"command": "uv run python script.py"},
        "tool_response": {
            "exit_code": 1,
            "stderr": "Traceback (most recent call last):\nValueError: bad",
            "stdout": "",
        },
    }
    proc = subprocess.run(
        [sys.executable, str(ROOT / ".claude" / "hooks" / "error-to-codex.py")],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "scripts/codex_research.py debug" in proc.stdout


def test_setup_status_is_codex_only() -> None:
    setup = (ROOT / "scripts" / "setup.sh").read_text(encoding="utf-8")
    assert "codex_available" in setup
    assert "gemini_available" not in setup


def test_shell_scripts_parse() -> None:
    subprocess.run(
        ["bash", "-n", "scripts/setup.sh", "scripts/update.sh"],
        cwd=ROOT,
        check=True,
    )
