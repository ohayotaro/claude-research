"""Reproducibility helpers used by every experiment script.

Copied into src/utils/repro.py by /init-research. Do not edit the source
under .claude/templates/ — that is the orchestrator template. To customize,
edit the copy under src/utils/.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import random
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _git_rev() -> tuple[str, bool]:
    try:
        rev = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
        dirty = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], stderr=subprocess.DEVNULL
        ).decode().strip())
        return rev + ("-dirty" if dirty else ""), not dirty
    except Exception:
        return "no-git", False


def _package_versions(packages: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in packages:
        try:
            out[p] = importlib.metadata.version(p)
        except importlib.metadata.PackageNotFoundError:
            out[p] = "not-installed"
    return out


def _detect_gpu() -> str | None:
    """Best-effort GPU detection via nvidia-smi. Returns None if unavailable."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
            text=True,
            timeout=5,
            stderr=subprocess.DEVNULL,
        )
        return out.strip() or None
    except Exception:
        return None


def make_run_id(args: dict[str, Any]) -> str:
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    h = hashlib.sha1(json.dumps(args, sort_keys=True, default=str).encode()).hexdigest()[:8]
    return f"{ts}_{h}"


def set_seed(seed: int) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    # Add framework-specific seeding here (torch, jax, tf) if installed.


def write_metadata(
    run_dir: Path,
    *,
    script: str,
    args: dict[str, Any],
    seed: int,
    started_at: str,
    finished_at: str | None = None,
    extra: dict[str, Any] | None = None,
    tracked_packages: list[str] | None = None,
) -> Path:
    rev, clean = _git_rev()
    hardware: dict[str, Any] = {"cpu_count": os.cpu_count()}
    gpu = _detect_gpu()
    if gpu is not None:
        hardware["gpu"] = gpu
    md = {
        "run_id": run_dir.name,
        "started_at": started_at,
        "finished_at": finished_at,
        "script": script,
        "args": args,
        "seed": seed,
        "git_rev": rev,
        "git_clean": clean,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "package_versions": _package_versions(
            tracked_packages or ["numpy", "scipy", "pandas", "matplotlib", "statsmodels"]
        ),
        "hardware": hardware,
    }
    if extra:
        md.update(extra)
    run_dir.mkdir(parents=True, exist_ok=True)
    p = run_dir / "metadata.json"
    p.write_text(json.dumps(md, indent=2, default=str), encoding="utf-8")
    return p
