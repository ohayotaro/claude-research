from __future__ import annotations

import importlib.util
import json
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
        if cmd[1:] == ["--version"]:
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


def test_profile_resolves_effort() -> None:
    runner = load_runner()
    assert runner.select_effort("build", None, {}, profile="fast") == runner.Selection(
        "medium", "profile"
    )
    assert runner.select_effort("review", None, {}, profile="deep") == runner.Selection(
        "xhigh", "profile"
    )


def test_profile_resolves_model_from_env() -> None:
    runner = load_runner()
    assert runner.select_model(
        "build", None, {"CODEX_STANDARD_MODEL": "o3"}, profile="standard"
    ) == runner.Selection("o3", "CODEX_STANDARD_MODEL")


def test_profile_model_falls_through_to_phase_env() -> None:
    runner = load_runner()
    assert runner.select_model(
        "build", None, {"CODEX_BUILD_MODEL": "o3"}, profile="standard"
    ) == runner.Selection("o3", "CODEX_BUILD_MODEL")


def test_explicit_model_overrides_profile() -> None:
    runner = load_runner()
    assert runner.select_model(
        "build", "custom-model", {"CODEX_FAST_MODEL": "o3"}, profile="fast"
    ) == runner.Selection("custom-model", "cli")


def test_profile_and_effort_mutually_exclusive(capsys: pytest.CaptureFixture[str]) -> None:
    runner = load_runner()
    assert runner.main(["build", "task-1", "--profile", "fast", "--effort", "high"]) == 1
    assert "cannot combine --profile with --effort" in capsys.readouterr().err


def test_invalid_profile_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    runner = load_runner()
    with pytest.raises(SystemExit) as exc:
        runner.main(["build", "task-1", "--profile", "invalid"])
    assert exc.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


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


def test_state_json_records_profile(tmp_path: Path) -> None:
    runner = load_runner()
    fake = FakeRunner()
    config = runner.phase_config(
        tmp_path,
        "build",
        "task-1",
        prompt_file="-",
        model=None,
        effort=None,
        profile="fast",
        env={},
        stdin_text="brief",
    )
    assert runner.run_phase(tmp_path, "task-1", config, timeout=10, runner=fake) == 0
    state = json.loads(
        (tmp_path / ".claude" / "tasks" / "task-1" / "state.json").read_text(
            encoding="utf-8"
        )
    )
    assert state["requested_profile"] == "fast"


def test_reviewer_effort_warning(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    runner = load_runner()
    directory = tmp_path / ".claude" / "tasks" / "task-1"
    directory.mkdir(parents=True)
    events = [
        {"event": "phase_started", "phase": "build", "effort": "high"},
        {"event": "phase_finished", "phase": "build", "status": "succeeded"},
    ]
    (directory / "events.jsonl").write_text(
        "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n",
        encoding="utf-8",
    )

    runner.warn_if_review_below_build(directory, "medium")
    assert "review effort (medium) is lower than build effort (high)" in capsys.readouterr().err

    runner.warn_if_review_below_build(directory, "high")
    assert capsys.readouterr().err == ""


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


def write_claude_md(root: Path, zone_b_yaml: str) -> None:
    root.joinpath("CLAUDE.md").write_text(
        "<!-- ZONE_B_BEGIN -->\n"
        "## Zone B - Project Configuration\n\n"
        "```yaml\n"
        f"{zone_b_yaml}"
        "\n```\n"
        "<!-- ZONE_B_END -->\n",
        encoding="utf-8",
    )


def test_zone_b_scalar_codex_auto(tmp_path: Path) -> None:
    runner = load_runner()
    write_claude_md(
        tmp_path,
        "status: initialized\nexternal_cli:\n  codex: auto\n",
    )
    config = runner.load_zone_b_config(tmp_path)
    assert config["command"] == "codex"
    assert config["default_model"] is None
    assert config["default_effort"] is None
    assert config["profiles"] == runner.PROFILES


def test_zone_b_object_config(tmp_path: Path) -> None:
    runner = load_runner()
    write_claude_md(
        tmp_path,
        "status: initialized\n"
        "external_cli:\n"
        "  codex:\n"
        "    command: /opt/bin/codex\n"
        "    default_model: gpt-test\n"
        "    default_effort: low\n"
        "    profiles:\n"
        "      fast: minimal\n"
        "      standard: medium\n"
        "      deep: high\n",
    )
    config = runner.load_zone_b_config(tmp_path)
    assert config["command"] == "/opt/bin/codex"
    assert config["default_model"] == "gpt-test"
    assert config["default_effort"] == "low"
    assert config["profiles"]["fast"] == "minimal"
    phase = runner.phase_config(
        tmp_path,
        "build",
        "task-1",
        prompt_file="-",
        model=None,
        effort=None,
        profile="deep",
        env={},
        stdin_text="brief",
        zone_b_config=config,
    )
    assert phase.command == runner.Selection("/opt/bin/codex", "zone_b_command")
    assert phase.model == runner.Selection("gpt-test", "zone_b_default_model")
    assert phase.effort == runner.Selection("high", "profile")
    assert runner.build_codex_command(tmp_path, phase)[0] == "/opt/bin/codex"


def test_zone_b_invalid_effort_graceful(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    runner = load_runner()
    write_claude_md(
        tmp_path,
        "status: initialized\n"
        "external_cli:\n"
        "  codex:\n"
        "    default_effort: turbo\n",
    )
    config = runner.load_zone_b_config(tmp_path)
    assert config["default_effort"] is None
    phase = runner.phase_config(
        tmp_path,
        "build",
        "task-1",
        prompt_file="-",
        model=None,
        effort=None,
        env={},
        stdin_text="brief",
        zone_b_config=config,
    )
    assert phase.effort == runner.Selection("high", "phase_default")
    err = capsys.readouterr().err
    assert "default_effort" in err
    assert "turbo" in err


def test_zone_b_invalid_profile_effort_graceful(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    runner = load_runner()
    write_claude_md(
        tmp_path,
        "status: initialized\n"
        "external_cli:\n"
        "  codex:\n"
        "    profiles:\n"
        "      fast: turbo\n",
    )
    config = runner.load_zone_b_config(tmp_path)
    assert config["profiles"]["fast"] == runner.PROFILES["fast"]
    phase = runner.phase_config(
        tmp_path,
        "build",
        "task-1",
        prompt_file="-",
        model=None,
        effort=None,
        profile="fast",
        env={},
        stdin_text="brief",
        zone_b_config=config,
    )
    assert phase.effort == runner.Selection("medium", "profile")
    err = capsys.readouterr().err
    assert "profiles" in err
    assert "turbo" in err


def test_zone_b_precedence_cli_over_zone_b(tmp_path: Path) -> None:
    runner = load_runner()
    config = {
        "command": "zone-codex",
        "default_model": "zone-model",
        "default_effort": "low",
        "profiles": runner.PROFILES,
    }
    phase = runner.phase_config(
        tmp_path,
        "review",
        "task-1",
        prompt_file="-",
        model="cli-model",
        effort="high",
        env={},
        stdin_text="brief",
        zone_b_config=config,
    )
    assert phase.model == runner.Selection("cli-model", "cli")
    assert phase.effort == runner.Selection("high", "cli")


def test_zone_b_precedence_env_over_zone_b(tmp_path: Path) -> None:
    runner = load_runner()
    config = {
        "command": "zone-codex",
        "default_model": "zone-model",
        "default_effort": "low",
        "profiles": runner.PROFILES,
    }
    phase = runner.phase_config(
        tmp_path,
        "build",
        "task-1",
        prompt_file="-",
        model=None,
        effort=None,
        env={
            "CODEX_CLI": "env-codex",
            "CODEX_BUILD_MODEL": "env-model",
            "CODEX_BUILD_EFFORT": "medium",
        },
        stdin_text="brief",
        zone_b_config=config,
    )
    assert phase.command == runner.Selection("env-codex", "CODEX_CLI")
    assert phase.model == runner.Selection("env-model", "CODEX_BUILD_MODEL")
    assert phase.effort == runner.Selection("medium", "CODEX_BUILD_EFFORT")


def test_zone_b_missing_graceful(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    runner = load_runner()
    config = runner.load_zone_b_config(tmp_path)
    assert config["command"] == "codex"
    assert "CLAUDE.md not found" in capsys.readouterr().err


def test_zone_b_malformed_graceful(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    runner = load_runner()
    write_claude_md(tmp_path, "external_cli: [bad\n")
    config = runner.load_zone_b_config(tmp_path)
    assert config["command"] == "codex"
    assert "malformed Zone B" in capsys.readouterr().err
