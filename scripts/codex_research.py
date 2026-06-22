#!/usr/bin/env python3
"""Centralized Codex runner for research orchestration tasks."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

STATE_VALUES = {"queued", "running", "succeeded", "failed", "blocked", "cancelled"}
PHASE_SANDBOX = {
    "plan": "read-only",
    "build": "workspace-write",
    "review": "read-only",
    "debug": "workspace-write",
}
PHASE_OUTPUT = {
    "plan": "plan.md",
    "build": "build-result.md",
    "review": "review.md",
    "debug": "debug-result.md",
}
PHASE_EFFORT_ENV = {
    "plan": ("CODEX_PLAN_MODEL", "CODEX_PLAN_EFFORT"),
    "build": ("CODEX_BUILD_MODEL", "CODEX_BUILD_EFFORT"),
    "review": ("CODEX_REVIEW_MODEL", "CODEX_REVIEW_EFFORT"),
    "debug": ("CODEX_DEBUG_MODEL", "CODEX_DEBUG_EFFORT"),
}
PHASE_DEFAULT_EFFORT = {
    "plan": "high",
    "build": "high",
    "review": "high",
    "debug": "medium",
}
ALLOWED_EFFORTS = {"minimal", "low", "medium", "high", "xhigh"}
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
SECRET_KEY_RE = re.compile(r"(token|secret|password|credential|api[_-]?key)", re.IGNORECASE)
SECRET_VALUE_RE = re.compile(
    r"(?i)(token|secret|password|credential|api[_-]?key)\s*[:=]\s*([^\s,;]+)"
)


class CommandRunner(Protocol):
    """Minimal protocol for subprocess execution, injectable in tests."""

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
        ...


@dataclass(frozen=True)
class Selection:
    value: str | None
    source: str


@dataclass(frozen=True)
class PhaseConfig:
    phase: str
    sandbox: str
    model: Selection
    effort: Selection
    output_path: Path
    prompt_text: str


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def repo_root_from(path: Path) -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=path,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode == 0:
        return Path(proc.stdout.strip()).resolve()
    return path.resolve()


def validate_task_id(task_id: str) -> str:
    if not TASK_ID_RE.match(task_id):
        raise ValueError(f"invalid task id: {task_id!r}")
    if ".." in task_id.split("."):
        raise ValueError(f"invalid task id: {task_id!r}")
    return task_id


def safe_repo_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = repo_root / path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"path escapes repository: {value}") from exc
    return resolved


def task_dir(repo_root: Path, task_id: str) -> Path:
    validate_task_id(task_id)
    directory = repo_root / ".claude" / "tasks" / task_id
    resolved = directory.resolve()
    resolved.relative_to(repo_root)
    return resolved


def redact(value: Any) -> Any:
    """Redact secret-looking keys and values without preserving raw command output."""

    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if SECRET_KEY_RE.search(str(key)):
                sanitized[str(key)] = "[REDACTED]"
            else:
                sanitized[str(key)] = redact(item)
        return sanitized
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        text = SECRET_VALUE_RE.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)
        if len(text) > 2000:
            return text[:2000] + "...[truncated]"
        return text
    return value


def git_head(repo_root: Path, runner: CommandRunner = subprocess) -> str:
    proc = runner.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        return "unknown"
    return proc.stdout.strip() or "unknown"


def codex_version(repo_root: Path, runner: CommandRunner = subprocess) -> str:
    proc = runner.run(
        ["codex", "--version"],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        return "unavailable"
    return proc.stdout.strip() or "unavailable"


def select_model(phase: str, explicit: str | None, env: dict[str, str]) -> Selection:
    phase_model_env, _ = PHASE_EFFORT_ENV[phase]
    if explicit:
        return Selection(explicit, "cli")
    if env.get(phase_model_env):
        return Selection(env[phase_model_env], phase_model_env)
    if env.get("CODEX_MODEL"):
        return Selection(env["CODEX_MODEL"], "CODEX_MODEL")
    return Selection(None, "user_default")


def select_effort(phase: str, explicit: str | None, env: dict[str, str]) -> Selection:
    _, phase_effort_env = PHASE_EFFORT_ENV[phase]
    if explicit:
        source = "cli"
        value = explicit
    elif env.get(phase_effort_env):
        source = phase_effort_env
        value = env[phase_effort_env]
    elif env.get("CODEX_EFFORT"):
        source = "CODEX_EFFORT"
        value = env["CODEX_EFFORT"]
    else:
        source = "phase_default"
        value = PHASE_DEFAULT_EFFORT[phase]

    if value not in ALLOWED_EFFORTS:
        raise ValueError(
            f"unsupported Codex effort {value!r}; expected one of {sorted(ALLOWED_EFFORTS)}"
        )
    return Selection(value, source)


def read_prompt(repo_root: Path, prompt_file: str | None, stdin_text: str | None) -> str:
    if prompt_file is None or prompt_file == "-":
        text = stdin_text if stdin_text is not None else sys.stdin.read()
    else:
        path = safe_repo_path(repo_root, prompt_file)
        text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("prompt is empty")
    return text


def phase_config(
    repo_root: Path,
    phase: str,
    task_id: str,
    *,
    prompt_file: str | None,
    model: str | None,
    effort: str | None,
    env: dict[str, str],
    stdin_text: str | None = None,
) -> PhaseConfig:
    if phase not in PHASE_SANDBOX:
        raise ValueError(f"unknown phase: {phase}")
    directory = task_dir(repo_root, task_id)
    prompt_text = read_prompt(repo_root, prompt_file, stdin_text)
    return PhaseConfig(
        phase=phase,
        sandbox=PHASE_SANDBOX[phase],
        model=select_model(phase, model, env),
        effort=select_effort(phase, effort, env),
        output_path=directory / PHASE_OUTPUT[phase],
        prompt_text=prompt_text,
    )


def build_codex_command(repo_root: Path, config: PhaseConfig) -> list[str]:
    cmd = [
        "codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--ephemeral",
        "--sandbox",
        config.sandbox,
        "--cd",
        str(repo_root),
        "--json",
        "--output-last-message",
        str(config.output_path),
    ]
    if config.model.value:
        cmd.extend(["--model", config.model.value])
    if config.effort.value:
        cmd.extend(["--config", f'model_reasoning_effort="{config.effort.value}"'])
    cmd.append("-")
    return cmd


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(redact(event), sort_keys=True) + "\n")


def write_state(
    state_path: Path,
    *,
    task_id: str,
    phase: str,
    status: str,
    started_at: str,
    finished_at: str | None,
    exit_code: int | None,
    codex_version_value: str,
    sandbox: str,
    model: Selection,
    effort: Selection,
    git_head_before: str,
    git_head_after: str | None,
    error: str | None = None,
) -> None:
    if status not in STATE_VALUES:
        raise ValueError(f"invalid state: {status}")
    data: dict[str, Any] = {
        "schema_version": "1.0",
        "task_id": task_id,
        "phase": phase,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "exit_code": exit_code,
        "codex_cli_version": codex_version_value,
        "sandbox": sandbox,
        "requested_model": model.value,
        "model_selection_source": model.source,
        "requested_effort": effort.value,
        "effort_selection_source": effort.source,
        "git_head_before": git_head_before,
        "git_head_after": git_head_after,
    }
    if error:
        data["error"] = error
    write_json(state_path, redact(data))


def _parse_jsonl(stdout: str, events_path: Path) -> list[str]:
    errors: list[str] = []
    for line_no, line in enumerate(stdout.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            errors.append(f"malformed JSONL on stdout line {line_no}")
            continue
        if isinstance(event, dict):
            append_event(events_path, event)
        else:
            errors.append(f"JSONL line {line_no} is not an object")
    return errors


def run_phase(
    repo_root: Path,
    task_id: str,
    config: PhaseConfig,
    *,
    timeout: int | None,
    runner: CommandRunner = subprocess,
) -> int:
    directory = task_dir(repo_root, task_id)
    directory.mkdir(parents=True, exist_ok=True)
    state_path = directory / "state.json"
    events_path = directory / "events.jsonl"
    brief_path = directory / "brief.md"
    if config.phase == "plan":
        brief_path.write_text(config.prompt_text, encoding="utf-8")
    if config.output_path.exists():
        config.output_path.unlink()

    started_at = utc_now()
    git_before = git_head(repo_root, runner)
    version = codex_version(repo_root, runner)
    write_state(
        state_path,
        task_id=task_id,
        phase=config.phase,
        status="running",
        started_at=started_at,
        finished_at=None,
        exit_code=None,
        codex_version_value=version,
        sandbox=config.sandbox,
        model=config.model,
        effort=config.effort,
        git_head_before=git_before,
        git_head_after=None,
    )
    append_event(
        events_path,
        {
            "time": started_at,
            "event": "phase_started",
            "phase": config.phase,
            "sandbox": config.sandbox,
            "model_source": config.model.source,
            "effort_source": config.effort.source,
        },
    )

    cmd = build_codex_command(repo_root, config)
    try:
        proc = runner.run(
            cmd,
            cwd=repo_root,
            input=config.prompt_text,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        jsonl_errors = _parse_jsonl(proc.stdout or "", events_path)
        output_exists = config.output_path.exists() and bool(
            config.output_path.read_text(encoding="utf-8").strip()
        )
        error: str | None = None
        status = "succeeded"
        if proc.returncode != 0:
            status = "failed"
            error = f"codex exited with {proc.returncode}"
        elif not output_exists:
            status = "failed"
            error = "codex produced an empty final message"
        elif jsonl_errors:
            status = "failed"
            error = "; ".join(jsonl_errors)
        exit_code: int | None = proc.returncode
    except subprocess.TimeoutExpired:
        status = "failed"
        error = "codex execution timed out"
        exit_code = None
    except KeyboardInterrupt:
        status = "cancelled"
        error = "interrupted"
        exit_code = None

    finished_at = utc_now()
    git_after = git_head(repo_root, runner)
    write_state(
        state_path,
        task_id=task_id,
        phase=config.phase,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        exit_code=exit_code,
        codex_version_value=version,
        sandbox=config.sandbox,
        model=config.model,
        effort=config.effort,
        git_head_before=git_before,
        git_head_after=git_after,
        error=error,
    )
    append_event(
        events_path,
        {
            "time": finished_at,
            "event": "phase_finished",
            "phase": config.phase,
            "status": status,
            "exit_code": exit_code,
            "error": error,
        },
    )
    return 0 if status == "succeeded" else 1


def print_status(repo_root: Path, task_id: str) -> int:
    state_path = task_dir(repo_root, task_id) / "state.json"
    if not state_path.exists():
        print(f"no state for task {task_id}", file=sys.stderr)
        return 1
    print(state_path.read_text(encoding="utf-8"), end="")
    return 0


def collect_task(repo_root: Path, task_id: str) -> int:
    directory = task_dir(repo_root, task_id)
    state_path = directory / "state.json"
    if not state_path.exists():
        print(f"no state for task {task_id}", file=sys.stderr)
        return 1
    state = json.loads(state_path.read_text(encoding="utf-8"))
    known_artifacts = {
        "brief.md",
        "plan.md",
        "build-result.md",
        "review.md",
        "debug-result.md",
    }
    result = {
        "state": state,
        "artifacts": sorted(
            str(path.relative_to(repo_root))
            for path in directory.glob("*")
            if path.name in known_artifacts
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _phase_command(args: argparse.Namespace) -> int:
    repo_root = repo_root_from(Path.cwd())
    try:
        config = phase_config(
            repo_root,
            args.phase,
            args.task_id,
            prompt_file=args.prompt_file,
            model=args.model,
            effort=args.effort,
            env=dict(os.environ),
        )
    except ValueError as exc:
        directory = task_dir(repo_root, args.task_id) if TASK_ID_RE.match(args.task_id) else None
        if directory is not None:
            write_json(
                directory / "state.json",
                {
                    "schema_version": "1.0",
                    "task_id": args.task_id,
                    "phase": args.phase,
                    "status": "blocked",
                    "error": str(exc),
                    "finished_at": utc_now(),
                },
            )
        print(f"blocked: {exc}", file=sys.stderr)
        return 2
    return run_phase(repo_root, args.task_id, config, timeout=args.timeout)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    for phase in ["plan", "build", "review", "debug"]:
        phase_parser = subcommands.add_parser(phase)
        phase_parser.set_defaults(func=_phase_command, phase=phase)
        phase_parser.add_argument("task_id")
        phase_parser.add_argument("--prompt-file", default="-")
        phase_parser.add_argument("--model")
        phase_parser.add_argument("--effort")
        phase_parser.add_argument("--timeout", type=int)

    status = subcommands.add_parser("status")
    status.add_argument("task_id")
    status.set_defaults(func=lambda args: print_status(repo_root_from(Path.cwd()), args.task_id))

    collect = subcommands.add_parser("collect")
    collect.add_argument("task_id")
    collect.set_defaults(func=lambda args: collect_task(repo_root_from(Path.cwd()), args.task_id))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
