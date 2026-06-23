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

import yaml

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
PROFILES: dict[str, str] = {
    "fast": "medium",
    "standard": "high",
    "deep": "xhigh",
}
PROFILE_MODEL_ENV: dict[str, str] = {
    "fast": "CODEX_FAST_MODEL",
    "standard": "CODEX_STANDARD_MODEL",
    "deep": "CODEX_DEEP_MODEL",
}
ALLOWED_EFFORTS = {"minimal", "low", "medium", "high", "xhigh"}
EFFORT_ORDER = {"minimal": 0, "low": 1, "medium": 2, "high": 3, "xhigh": 4}
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
    command: Selection
    model: Selection
    effort: Selection
    output_path: Path
    prompt_text: str
    profile: str | None = None


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


def _default_zone_b_config() -> dict[str, Any]:
    return {
        "command": "codex",
        "_command_source": "default",
        "default_model": None,
        "default_effort": None,
        "profiles": dict(PROFILES),
    }


def _extract_zone_b_yaml(text: str) -> str:
    zone_match = re.search(
        r"<!-- ZONE_B_BEGIN -->(?P<body>.*?)<!-- ZONE_B_END -->",
        text,
        re.DOTALL,
    )
    if not zone_match:
        raise ValueError("Zone B markers not found")
    fence_match = re.search(
        r"```yaml\s*(?P<yaml>.*?)```",
        zone_match.group("body"),
        re.DOTALL,
    )
    if not fence_match:
        raise ValueError("Zone B yaml fence not found")
    return fence_match.group("yaml")


def load_zone_b_config(repo_root: Path) -> dict[str, Any]:
    """Load Codex external CLI defaults from CLAUDE.md Zone B."""

    config = _default_zone_b_config()
    claude_md = repo_root / "CLAUDE.md"
    try:
        text = claude_md.read_text(encoding="utf-8")
    except FileNotFoundError:
        print("[zone-b] Warning: CLAUDE.md not found; using Codex defaults.", file=sys.stderr)
        return config

    try:
        raw_yaml = _extract_zone_b_yaml(text)
        zone_b = yaml.safe_load(raw_yaml)
    except Exception as exc:
        print(f"[zone-b] Warning: malformed Zone B; using Codex defaults: {exc}", file=sys.stderr)
        return config

    if not isinstance(zone_b, dict):
        print("[zone-b] Warning: Zone B is not a mapping; using Codex defaults.", file=sys.stderr)
        return config

    external_cli = zone_b.get("external_cli")
    if external_cli is None:
        return config
    if not isinstance(external_cli, dict):
        print(
            "[zone-b] Warning: external_cli is not a mapping; using Codex defaults.",
            file=sys.stderr,
        )
        return config

    codex = external_cli.get("codex")
    if codex is None:
        return config
    if codex == "auto":
        config["_command_source"] = "zone_b_command"
        return config
    if isinstance(codex, str):
        print(
            "[zone-b] Warning: external_cli.codex scalar is not 'auto'; using Codex defaults.",
            file=sys.stderr,
        )
        return config
    if not isinstance(codex, dict):
        print(
            "[zone-b] Warning: external_cli.codex is not a mapping; using Codex defaults.",
            file=sys.stderr,
        )
        return config

    command = codex.get("command")
    if isinstance(command, str) and command.strip():
        config["command"] = command.strip()
        config["_command_source"] = "zone_b_command"

    default_model = codex.get("default_model")
    if default_model is None or isinstance(default_model, str):
        config["default_model"] = default_model
    else:
        print(
            "[zone-b] Warning: external_cli.codex.default_model must be string or null; "
            "ignoring.",
            file=sys.stderr,
        )

    default_effort = codex.get("default_effort")
    if default_effort is None:
        config["default_effort"] = None
    elif isinstance(default_effort, str):
        if default_effort in ALLOWED_EFFORTS:
            config["default_effort"] = default_effort
        else:
            print(
                "[zone-b] Warning: external_cli.codex.default_effort "
                f"{default_effort!r} is invalid; using Codex defaults.",
                file=sys.stderr,
            )
    else:
        print(
            "[zone-b] Warning: external_cli.codex.default_effort must be string or null; "
            "ignoring.",
            file=sys.stderr,
        )

    profiles = codex.get("profiles")
    if profiles is not None:
        if isinstance(profiles, dict):
            merged_profiles = dict(PROFILES)
            for name, effort in profiles.items():
                if isinstance(name, str) and isinstance(effort, str):
                    if effort in ALLOWED_EFFORTS:
                        merged_profiles[name] = effort
                    else:
                        print(
                            "[zone-b] Warning: external_cli.codex.profiles "
                            f"{name!r} effort {effort!r} is invalid; using Codex defaults.",
                            file=sys.stderr,
                        )
                else:
                    print(
                        "[zone-b] Warning: external_cli.codex.profiles entries must be "
                        "string-to-string; ignoring invalid entry.",
                        file=sys.stderr,
                    )
            config["profiles"] = merged_profiles
        else:
            print(
                "[zone-b] Warning: external_cli.codex.profiles must be a mapping; ignoring.",
                file=sys.stderr,
            )

    return config


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


def codex_version(
    repo_root: Path,
    runner: CommandRunner = subprocess,
    command: str = "codex",
) -> str:
    proc = runner.run(
        [command, "--version"],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        return "unavailable"
    return proc.stdout.strip() or "unavailable"


def select_model(
    phase: str,
    explicit: str | None,
    env: dict[str, str],
    profile: str | None = None,
    zone_b_config: dict[str, Any] | None = None,
) -> Selection:
    phase_model_env, _ = PHASE_EFFORT_ENV[phase]
    if explicit:
        return Selection(explicit, "cli")
    if profile:
        profile_model_env = PROFILE_MODEL_ENV[profile]
        if env.get(profile_model_env):
            return Selection(env[profile_model_env], profile_model_env)
    if env.get(phase_model_env):
        return Selection(env[phase_model_env], phase_model_env)
    if env.get("CODEX_MODEL"):
        return Selection(env["CODEX_MODEL"], "CODEX_MODEL")
    if zone_b_config and zone_b_config.get("default_model"):
        return Selection(str(zone_b_config["default_model"]), "zone_b_default_model")
    return Selection(None, "user_default")


def select_effort(
    phase: str,
    explicit: str | None,
    env: dict[str, str],
    profile: str | None = None,
    zone_b_config: dict[str, Any] | None = None,
) -> Selection:
    _, phase_effort_env = PHASE_EFFORT_ENV[phase]
    if profile:
        source = "profile"
        profiles = (
            zone_b_config.get("profiles", PROFILES)
            if zone_b_config is not None
            else PROFILES
        )
        value = profiles[profile]
    elif explicit:
        source = "cli"
        value = explicit
    elif env.get(phase_effort_env):
        source = phase_effort_env
        value = env[phase_effort_env]
    elif env.get("CODEX_EFFORT"):
        source = "CODEX_EFFORT"
        value = env["CODEX_EFFORT"]
    elif zone_b_config and zone_b_config.get("default_effort"):
        source = "zone_b_default_effort"
        value = str(zone_b_config["default_effort"])
    else:
        source = "phase_default"
        value = PHASE_DEFAULT_EFFORT[phase]

    if value not in ALLOWED_EFFORTS:
        raise ValueError(
            f"unsupported Codex effort {value!r}; expected one of {sorted(ALLOWED_EFFORTS)}"
        )
    return Selection(value, source)


def select_command(env: dict[str, str], zone_b_config: dict[str, Any] | None = None) -> Selection:
    if env.get("CODEX_CLI"):
        return Selection(env["CODEX_CLI"], "CODEX_CLI")
    if zone_b_config and zone_b_config.get("command"):
        return Selection(
            str(zone_b_config["command"]),
            str(zone_b_config.get("_command_source", "zone_b_command")),
        )
    return Selection("codex", "default")


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
    profile: str | None = None,
    env: dict[str, str],
    stdin_text: str | None = None,
    zone_b_config: dict[str, Any] | None = None,
) -> PhaseConfig:
    if phase not in PHASE_SANDBOX:
        raise ValueError(f"unknown phase: {phase}")
    directory = task_dir(repo_root, task_id)
    prompt_text = read_prompt(repo_root, prompt_file, stdin_text)
    return PhaseConfig(
        phase=phase,
        sandbox=PHASE_SANDBOX[phase],
        command=select_command(env, zone_b_config),
        model=select_model(phase, model, env, profile, zone_b_config),
        effort=select_effort(phase, effort, env, profile, zone_b_config),
        profile=profile,
        output_path=directory / PHASE_OUTPUT[phase],
        prompt_text=prompt_text,
    )


def build_codex_command(repo_root: Path, config: PhaseConfig) -> list[str]:
    cmd = [
        config.command.value or "codex",
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
        cmd.extend(["--config", f"model_reasoning_effort={config.effort.value}"])
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
    requested_profile: str | None = None,
    command: Selection | None = None,
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
        "codex_command": command.value if command else "codex",
        "command_selection_source": command.source if command else "default",
        "sandbox": sandbox,
        "requested_profile": requested_profile,
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


def _latest_successful_build_effort(events_path: Path) -> str | None:
    if not events_path.exists():
        return None

    latest_started_effort: str | None = None
    latest_succeeded_effort: str | None = None
    for line in events_path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("phase") != "build":
            continue
        if event.get("event") == "phase_started":
            effort = event.get("effort")
            latest_started_effort = effort if isinstance(effort, str) else None
        elif event.get("event") == "phase_finished" and event.get("status") == "succeeded":
            latest_succeeded_effort = latest_started_effort
    return latest_succeeded_effort


def warn_if_review_below_build(directory: Path, review_effort: str) -> None:
    build_effort = _latest_successful_build_effort(directory / "events.jsonl")
    if build_effort is None:
        return
    if build_effort not in EFFORT_ORDER or review_effort not in EFFORT_ORDER:
        return
    if EFFORT_ORDER[review_effort] < EFFORT_ORDER[build_effort]:
        print(
            "[profile-routing] Warning: review effort "
            f"({review_effort}) is lower than build effort ({build_effort}) "
            f"for task {directory.name}. Consider using --profile standard or higher.",
            file=sys.stderr,
        )


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
    version = codex_version(repo_root, runner, config.command.value or "codex")
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
        command=config.command,
        model=config.model,
        effort=config.effort,
        git_head_before=git_before,
        git_head_after=None,
        requested_profile=config.profile,
    )
    append_event(
        events_path,
        {
            "time": started_at,
            "event": "phase_started",
            "phase": config.phase,
            "sandbox": config.sandbox,
            "model_source": config.model.source,
            "command_source": config.command.source,
            "effort": config.effort.value,
            "effort_source": config.effort.source,
        },
    )
    if config.phase == "review" and config.effort.value is not None:
        warn_if_review_below_build(directory, config.effort.value)

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
        command=config.command,
        model=config.model,
        effort=config.effort,
        git_head_before=git_before,
        git_head_after=git_after,
        requested_profile=config.profile,
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
    profile = getattr(args, "profile", None)
    if profile and args.effort:
        print(
            "error: cannot combine --profile with --effort; "
            "profile sets effort automatically",
            file=sys.stderr,
        )
        return 1
    zone_b_config = load_zone_b_config(repo_root)
    try:
        config = phase_config(
            repo_root,
            args.phase,
            args.task_id,
            prompt_file=args.prompt_file,
            model=args.model,
            effort=args.effort,
            profile=profile,
            env=dict(os.environ),
            zone_b_config=zone_b_config,
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
        if phase in {"build", "review", "debug"}:
            phase_parser.add_argument("--profile", choices=sorted(PROFILES))
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
