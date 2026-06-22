from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def load_runner() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "scripts" / "codex_research.py"
    spec = importlib.util.spec_from_file_location("codex_research", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeRunner:
    def __init__(
        self,
        *,
        exit_code: int = 0,
        stdout: str = '{"event":"ok"}\n',
        write_output: bool = True,
        raise_timeout: bool = False,
    ) -> None:
        self.exit_code = exit_code
        self.stdout = stdout
        self.write_output = write_output
        self.raise_timeout = raise_timeout
        self.calls: list[list[str]] = []

    def run(
        self,
        cmd: list[str],
        *,
        cwd: Path,
        input: str | None = None,
        text: bool = True,
        capture_output: bool = True,
        timeout: int | None = None,
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append(cmd)
        if cmd[:3] == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="abc123\n", stderr="")
        if cmd == ["codex", "--version"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="codex 1.2.3\n", stderr="")
        if self.raise_timeout:
            raise subprocess.TimeoutExpired(cmd, timeout or 0.0)
        if self.write_output and "--output-last-message" in cmd:
            output_path = Path(cmd[cmd.index("--output-last-message") + 1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("done\n", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, self.exit_code, stdout=self.stdout, stderr="")


def test_command_construction_by_phase(tmp_path: Path) -> None:
    runner = load_runner()
    for phase, sandbox in {
        "plan": "read-only",
        "build": "workspace-write",
        "review": "read-only",
        "debug": "workspace-write",
    }.items():
        config = runner.phase_config(
            tmp_path,
            phase,
            "task-1",
            prompt_file="-",
            model="gpt-test",
            effort="high",
            env={},
            stdin_text="brief",
        )
        cmd = runner.build_codex_command(tmp_path, config)
        assert cmd[:4] == ["codex", "--ask-for-approval", "never", "exec"]
        assert cmd[cmd.index("--sandbox") + 1] == sandbox
        assert "--ephemeral" in cmd
        assert "--json" in cmd
        assert "--output-last-message" in cmd
        assert cmd[-1] == "-"
        assert "gpt-test" in cmd


def test_omits_model_when_unset_and_uses_effort_precedence(tmp_path: Path) -> None:
    runner = load_runner()
    config = runner.phase_config(
        tmp_path,
        "review",
        "task-1",
        prompt_file="-",
        model=None,
        effort=None,
        env={"CODEX_EFFORT": "medium", "CODEX_REVIEW_EFFORT": "xhigh"},
        stdin_text="brief",
    )
    cmd = runner.build_codex_command(tmp_path, config)
    assert "--model" not in cmd
    assert config.effort.value == "xhigh"
    assert config.effort.source == "CODEX_REVIEW_EFFORT"


def test_invalid_effort_and_task_id_are_rejected(tmp_path: Path) -> None:
    runner = load_runner()
    with pytest.raises(ValueError, match="unsupported Codex effort"):
        runner.phase_config(
            tmp_path,
            "plan",
            "task-1",
            prompt_file="-",
            model=None,
            effort="tiny",
            env={},
            stdin_text="brief",
        )
    with pytest.raises(ValueError, match="invalid task id"):
        runner.validate_task_id("../escape")
    with pytest.raises(ValueError, match="path escapes repository"):
        runner.safe_repo_path(tmp_path, "../outside")


def test_run_phase_state_transitions_success(tmp_path: Path) -> None:
    runner = load_runner()
    fake = FakeRunner()
    config = runner.phase_config(
        tmp_path,
        "plan",
        "task-1",
        prompt_file="-",
        model=None,
        effort="high",
        env={},
        stdin_text="brief",
    )
    assert runner.run_phase(tmp_path, "task-1", config, timeout=10, runner=fake) == 0
    state = (tmp_path / ".claude" / "tasks" / "task-1" / "state.json").read_text(
        encoding="utf-8"
    )
    assert '"status": "succeeded"' in state
    assert '"sandbox": "read-only"' in state
    assert (tmp_path / ".claude" / "tasks" / "task-1" / "brief.md").exists()


@pytest.mark.parametrize(
    ("fake", "expected"),
    [
        (FakeRunner(exit_code=1), "codex exited with 1"),
        (FakeRunner(write_output=False), "empty final message"),
        (FakeRunner(stdout="not-json\n"), "malformed JSONL"),
        (FakeRunner(raise_timeout=True), "timed out"),
    ],
)
def test_run_phase_failure_states(tmp_path: Path, fake: FakeRunner, expected: str) -> None:
    runner = load_runner()
    config = runner.phase_config(
        tmp_path,
        "review",
        "task-1",
        prompt_file="-",
        model=None,
        effort="high",
        env={},
        stdin_text="brief",
    )
    assert runner.run_phase(tmp_path, "task-1", config, timeout=1, runner=fake) == 1
    state = (tmp_path / ".claude" / "tasks" / "task-1" / "state.json").read_text(
        encoding="utf-8"
    )
    assert '"status": "failed"' in state
    assert expected in state


def test_reviewer_is_read_only_and_builder_is_write_capable(tmp_path: Path) -> None:
    runner = load_runner()
    review = runner.phase_config(
        tmp_path,
        "review",
        "review-task",
        prompt_file="-",
        model=None,
        effort="high",
        env={},
        stdin_text="review",
    )
    build = runner.phase_config(
        tmp_path,
        "build",
        "build-task",
        prompt_file="-",
        model=None,
        effort="high",
        env={},
        stdin_text="build",
    )
    assert review.sandbox == "read-only"
    assert build.sandbox == "workspace-write"


def test_redaction_removes_secret_values() -> None:
    runner = load_runner()
    redacted: dict[str, Any] = runner.redact(
        {"api_key": "abc", "message": "token: secret-value"}
    )
    assert redacted["api_key"] == "[REDACTED]"
    assert "secret-value" not in redacted["message"]
