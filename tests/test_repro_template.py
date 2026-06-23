from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_repro() -> ModuleType:
    path = ROOT / ".claude" / "templates" / "python" / "repro.py"
    spec = importlib.util.spec_from_file_location("repro_template", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_gpu_detection_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repro = load_repro()

    def fake_check_output(cmd: list[str], **kwargs: Any) -> bytes | str:
        if cmd[0] == "nvidia-smi":
            raise FileNotFoundError
        return b""

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    path = repro.write_metadata(
        tmp_path / "run-1",
        script="src/experiments/run.py",
        args={},
        seed=1,
        started_at="2026-06-23T00:00:00Z",
    )
    hardware = json.loads(path.read_text(encoding="utf-8"))["hardware"]
    assert "cpu_count" in hardware
    assert "gpu" not in hardware


def test_gpu_detection_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repro = load_repro()

    def fake_check_output(cmd: list[str], **kwargs: Any) -> bytes | str:
        if cmd[0] == "nvidia-smi":
            return "Test GPU, 555.55\n"
        if cmd[:3] == ["git", "rev-parse", "HEAD"]:
            return b"abc123\n"
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return b""
        return b""

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    path = repro.write_metadata(
        tmp_path / "run-1",
        script="src/experiments/run.py",
        args={},
        seed=1,
        started_at="2026-06-23T00:00:00Z",
    )
    hardware = json.loads(path.read_text(encoding="utf-8"))["hardware"]
    assert hardware["gpu"] == "Test GPU, 555.55"


def test_cpu_count_always_present(tmp_path: Path) -> None:
    repro = load_repro()
    path = repro.write_metadata(
        tmp_path / "run-1",
        script="src/experiments/run.py",
        args={},
        seed=1,
        started_at="2026-06-23T00:00:00Z",
    )
    hardware = json.loads(path.read_text(encoding="utf-8"))["hardware"]
    assert "cpu_count" in hardware
