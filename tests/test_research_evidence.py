from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


def load_evidence() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "scripts" / "research_evidence.py"
    spec = importlib.util.spec_from_file_location("research_evidence", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def valid_ledger(run_id: str = "run-1") -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "run_id": run_id,
        "generated_at": "2026-06-23T00:00:00Z",
        "git_rev": "abc123",
        "hypotheses": ["H1"],
        "results": [
            {
                "result_id": "R1",
                "hypothesis_id": "H1",
                "analysis_status": "confirmatory",
                "estimand": "mean difference",
                "test": "t-test",
                "n": 12,
                "estimate": 0.5,
                "effect_size": {"type": "cohens_d", "value": 0.2},
                "interval": {"level": 0.95, "lower": 0.1, "upper": 0.9},
                "p_value": None,
                "multiplicity_correction": None,
                "assumptions": [],
                "source_artifacts": ["results.csv"],
                "figure_paths": ["figures/main.png"],
            }
        ],
        "limitations": [],
    }


def test_validates_analysis_ledger(tmp_path: Path) -> None:
    evidence = load_evidence()
    ledger = tmp_path / "analysis.json"
    ledger.write_text(json.dumps(valid_ledger()), encoding="utf-8")
    assert evidence.validate_ledger(ledger) == []


def test_rejects_invalid_ledger_paths_and_status(tmp_path: Path) -> None:
    evidence = load_evidence()
    data = valid_ledger()
    result = data["results"][0]
    assert isinstance(result, dict)
    result["analysis_status"] = "maybe"
    result["source_artifacts"] = ["../raw.csv"]
    ledger = tmp_path / "analysis.json"
    ledger.write_text(json.dumps(data), encoding="utf-8")
    errors = evidence.validate_ledger(ledger)
    assert any("analysis_status" in error for error in errors)
    assert any("unsafe" in error for error in errors)


def test_trace_prose_result_ids(tmp_path: Path) -> None:
    evidence = load_evidence()
    run_dir = tmp_path / "data" / "results" / "run-1"
    run_dir.mkdir(parents=True)
    (run_dir / "analysis.json").write_text(json.dumps(valid_ledger()), encoding="utf-8")
    prose = tmp_path / "docs" / "research"
    prose.mkdir(parents=True)
    (prose / "analysis.md").write_text(
        "Supported claim [result:R1]. Missing claim [result:R2].",
        encoding="utf-8",
    )
    report = evidence.trace_prose_result_ids(tmp_path)
    assert "R1" in report.referenced_result_ids
    assert any("R2" in item for item in report.missing)


def test_trace_scoped_result_ids(tmp_path: Path) -> None:
    evidence = load_evidence()
    run_dir = tmp_path / "data" / "results" / "run-1"
    run_dir.mkdir(parents=True)
    (run_dir / "analysis.json").write_text(json.dumps(valid_ledger()), encoding="utf-8")
    prose = tmp_path / "docs" / "paper" / "main"
    prose.mkdir(parents=True)
    (prose / "draft.md").write_text("Claim [result:run-1:R1].", encoding="utf-8")
    report = evidence.trace_prose_result_ids(tmp_path)
    assert report.missing == []
    assert "run-1:R1" in report.referenced_scoped_result_ids
