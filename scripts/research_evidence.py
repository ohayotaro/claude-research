#!/usr/bin/env python3
"""Validate structured research evidence ledgers and prose traceability."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

RESULT_REF_RE = re.compile(
    r"\[result:(?P<first>[A-Za-z0-9_.-]+)(?::(?P<second>[A-Za-z0-9_.-]+))?\]"
)
VALID_STATUS = {"confirmatory", "exploratory", "failed", "inconclusive"}
REQUIRED_RESULT_KEYS = {
    "result_id",
    "hypothesis_id",
    "analysis_status",
    "estimand",
    "test",
    "n",
    "estimate",
    "effect_size",
    "interval",
    "p_value",
    "multiplicity_correction",
    "assumptions",
    "source_artifacts",
    "figure_paths",
}
REQUIRED_METADATA_KEYS = {
    "run_id",
    "started_at",
    "script",
    "args",
    "seed",
    "git_rev",
    "python_version",
    "platform",
    "package_versions",
}


@dataclass(frozen=True)
class TraceabilityReport:
    """Result-ID traceability summary for canonical prose."""

    known_result_ids: set[str]
    known_scoped_result_ids: set[str]
    referenced_result_ids: set[str]
    referenced_scoped_result_ids: set[str]
    missing: list[str]
    warnings: list[str]


def _load_json(path: Path) -> tuple[Any | None, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except FileNotFoundError:
        return None, [f"{path}: file does not exist"]
    except json.JSONDecodeError as exc:
        return None, [f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}"]


def _is_iso8601(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _is_safe_artifact_path(value: str) -> bool:
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def _require_string(obj: dict[str, Any], key: str, errors: list[str]) -> None:
    if not isinstance(obj.get(key), str) or not obj.get(key):
        errors.append(f"{key} must be a non-empty string")


def _validate_ledger_schema(path: Path) -> list[str]:
    """Return baseline schema errors for one `analysis.json` ledger."""

    data, errors = _load_json(path)
    if errors:
        return errors
    if not isinstance(data, dict):
        return [f"{path}: top-level value must be an object"]

    for key in ["schema_version", "run_id", "generated_at", "git_rev"]:
        _require_string(data, key, errors)
    if data.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")
    if isinstance(data.get("generated_at"), str) and not _is_iso8601(data["generated_at"]):
        errors.append("generated_at must be ISO-8601")

    hypotheses = data.get("hypotheses")
    if not isinstance(hypotheses, list) or not all(isinstance(h, str) for h in hypotheses):
        errors.append("hypotheses must be a list of strings")
        hypothesis_ids: set[str] = set()
    else:
        hypothesis_ids = set(hypotheses)

    limitations = data.get("limitations")
    if not isinstance(limitations, list) or not all(
        isinstance(item, str) for item in limitations
    ):
        errors.append("limitations must be a list of strings")

    results = data.get("results")
    if not isinstance(results, list) or not results:
        errors.append("results must be a non-empty list")
        return errors

    for index, result in enumerate(results):
        prefix = f"results[{index}]"
        if not isinstance(result, dict):
            errors.append(f"{prefix} must be an object")
            continue

        missing = REQUIRED_RESULT_KEYS - result.keys()
        if missing:
            errors.append(f"{prefix} missing required keys: {', '.join(sorted(missing))}")

        result_id = result.get("result_id")
        if not isinstance(result_id, str) or not result_id:
            errors.append(f"{prefix}.result_id must be a non-empty string")

        hypothesis_id = result.get("hypothesis_id")
        if not isinstance(hypothesis_id, str) or not hypothesis_id:
            errors.append(f"{prefix}.hypothesis_id must be a non-empty string")
        elif hypothesis_ids and hypothesis_id not in hypothesis_ids:
            errors.append(f"{prefix}.hypothesis_id is not listed in hypotheses")

        status = result.get("analysis_status")
        if status not in VALID_STATUS:
            errors.append(f"{prefix}.analysis_status must be one of {sorted(VALID_STATUS)}")

        for key in ["estimand", "test"]:
            if not isinstance(result.get(key), str) or not result.get(key):
                errors.append(f"{prefix}.{key} must be a non-empty string")

        n_value = result.get("n")
        if not isinstance(n_value, int) or n_value < 0:
            errors.append(f"{prefix}.n must be a non-negative integer")

        effect_size = result.get("effect_size")
        if not isinstance(effect_size, dict) or not isinstance(effect_size.get("type"), str):
            errors.append(f"{prefix}.effect_size must include a string type")
        elif "value" not in effect_size:
            errors.append(f"{prefix}.effect_size must include value")

        interval = result.get("interval")
        if not isinstance(interval, dict):
            errors.append(f"{prefix}.interval must be an object")
        else:
            level = interval.get("level")
            if not isinstance(level, int | float) or not 0 < float(level) < 1:
                errors.append(f"{prefix}.interval.level must be between 0 and 1")
            for key in ["lower", "upper"]:
                if key not in interval:
                    errors.append(f"{prefix}.interval.{key} is required")

        for key in ["assumptions", "source_artifacts", "figure_paths"]:
            value = result.get(key)
            if not isinstance(value, list):
                errors.append(f"{prefix}.{key} must be a list")
            elif key != "assumptions":
                bad = [
                    item
                    for item in value
                    if not isinstance(item, str) or not _is_safe_artifact_path(item)
                ]
                if bad:
                    errors.append(f"{prefix}.{key} contains unsafe or non-string paths")

    return errors


def _validate_ledger_strict_checks(path: Path) -> list[str]:
    """Return checks that are warnings unless strict mode is enabled."""

    data, load_errors = _load_json(path)
    if load_errors or not isinstance(data, dict):
        return []

    warnings: list[str] = []
    run_id = data.get("run_id")
    metadata_path = path.parent / "metadata.json"
    metadata, metadata_errors = _load_json(metadata_path)
    if metadata_errors:
        warnings.extend(metadata_errors)
    elif not isinstance(metadata, dict):
        warnings.append(f"{metadata_path}: top-level value must be an object")
    else:
        for key in sorted(REQUIRED_METADATA_KEYS):
            if key not in metadata:
                warnings.append(f"{metadata_path}: missing required key {key}")
        if isinstance(run_id, str) and metadata.get("run_id") != run_id:
            warnings.append(
                f"{metadata_path}: run_id {metadata.get('run_id')!r} does not match "
                f"ledger run_id {run_id!r}"
            )

    results = data.get("results")
    if not isinstance(results, list):
        return warnings

    seen_result_ids: set[str] = set()
    for index, result in enumerate(results):
        prefix = f"results[{index}]"
        if not isinstance(result, dict):
            continue

        result_id = result.get("result_id")
        if isinstance(result_id, str) and result_id:
            if result_id in seen_result_ids:
                warnings.append(f"{prefix}.result_id duplicates {result_id}")
            else:
                seen_result_ids.add(result_id)

        p_value = result.get("p_value")
        if p_value is not None and (
            not isinstance(p_value, int | float) or not 0 <= float(p_value) <= 1
        ):
            warnings.append(f"{prefix}.p_value must be null or between 0 and 1")

        interval = result.get("interval")
        if isinstance(interval, dict):
            lower = interval.get("lower")
            upper = interval.get("upper")
            if (
                isinstance(lower, int | float)
                and isinstance(upper, int | float)
                and float(lower) > float(upper)
            ):
                warnings.append(f"{prefix}.interval lower must be <= upper")

    return warnings


def validate_ledger(path: Path, *, strict: bool = False) -> list[str]:
    """Return validation errors for one `analysis.json` ledger."""

    errors = _validate_ledger_schema(path)
    if strict:
        errors.extend(_validate_ledger_strict_checks(path))
    return errors


def validate_ledger_warnings(path: Path) -> list[str]:
    """Return non-strict warnings for one `analysis.json` ledger."""

    return _validate_ledger_strict_checks(path)


def ledger_result_ids(repo_root: Path) -> tuple[set[str], set[str], dict[str, set[str]], list[str]]:
    """Collect unscoped and run-scoped result IDs from all ledgers."""

    result_ids: set[str] = set()
    scoped_result_ids: set[str] = set()
    runs_by_result_id: dict[str, set[str]] = {}
    errors: list[str] = []
    for ledger in sorted((repo_root / "data" / "results").glob("*/analysis.json")):
        ledger_errors = validate_ledger(ledger)
        if ledger_errors:
            errors.extend(f"{ledger}: {error}" for error in ledger_errors)
            continue
        data = json.loads(ledger.read_text(encoding="utf-8"))
        run_id = str(data["run_id"])
        for result in data["results"]:
            result_id = str(result["result_id"])
            result_ids.add(result_id)
            scoped_result_ids.add(f"{run_id}:{result_id}")
            runs_by_result_id.setdefault(result_id, set()).add(run_id)
    return result_ids, scoped_result_ids, runs_by_result_id, errors


def _is_exempt_paper_path(path: Path, repo_root: Path) -> bool:
    """Exclude submission bundles and changelog from citation/result scanning."""
    try:
        rel = path.relative_to(repo_root / "docs" / "paper")
    except ValueError:
        return False
    rel_parts = rel.parts
    if "submissions" in rel_parts:
        return True
    return bool(rel_parts and rel_parts[-1] == "changelog.md")


def prose_files(repo_root: Path) -> list[Path]:
    """Return canonical prose files that may cite result IDs."""

    files: list[Path] = []
    for root in [repo_root / "docs" / "research", repo_root / "docs" / "paper"]:
        if not root.exists():
            continue
        for path in root.rglob("*.md"):
            if path.is_file() and not _is_exempt_paper_path(path, repo_root):
                files.append(path)
        for path in root.rglob("*.tex"):
            if path.is_file() and not _is_exempt_paper_path(path, repo_root):
                files.append(path)
    release_root = repo_root / "docs" / "release"
    if release_root.exists():
        for path in release_root.glob("*/*.md"):
            if path.is_file():
                files.append(path)
        for path in release_root.rglob("datacard.md"):
            if path.is_file():
                files.append(path)
    return sorted(set(files))


def trace_prose_result_ids(repo_root: Path) -> TraceabilityReport:
    """Find prose result references that are absent from structured ledgers."""

    known, known_scoped, runs_by_result_id, ledger_errors = ledger_result_ids(repo_root)
    missing = list(ledger_errors)
    warnings: list[str] = []
    referenced: set[str] = set()
    referenced_scoped: set[str] = set()

    for path in prose_files(repo_root):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(repo_root)
        for match in RESULT_REF_RE.finditer(text):
            first = match.group("first")
            second = match.group("second")
            if second is None:
                referenced.add(first)
                if first not in known:
                    missing.append(f"{rel}: unknown result ID {first}")
                elif len(runs_by_result_id.get(first, set())) > 1:
                    runs = ", ".join(sorted(runs_by_result_id[first]))
                    warnings.append(
                        f"{rel}: ambiguous unscoped result ID {first}; present in runs {runs}"
                    )
            else:
                scoped = f"{first}:{second}"
                referenced_scoped.add(scoped)
                if scoped not in known_scoped:
                    missing.append(f"{rel}: unknown scoped result ID {scoped}")

    return TraceabilityReport(
        known_result_ids=known,
        known_scoped_result_ids=known_scoped,
        referenced_result_ids=referenced,
        referenced_scoped_result_ids=referenced_scoped,
        missing=missing,
        warnings=warnings,
    )


def _cmd_validate_ledger(args: argparse.Namespace) -> int:
    path = Path(args.path)
    warnings = [] if args.strict else validate_ledger_warnings(path)
    errors = validate_ledger(path, strict=args.strict)
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("ledger: ok")
    return 0


def _cmd_trace_prose(args: argparse.Namespace) -> int:
    report = trace_prose_result_ids(Path(args.repo_root).resolve())
    for warning in report.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    if report.missing:
        for error in report.missing:
            print(error, file=sys.stderr)
        return 1
    print("result traceability: ok")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate-ledger")
    validate.add_argument("path")
    validate.add_argument("--strict", action="store_true")
    validate.set_defaults(func=_cmd_validate_ledger)

    trace = subcommands.add_parser("trace-prose")
    trace.add_argument("--repo-root", default=".")
    trace.set_defaults(func=_cmd_trace_prose)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
