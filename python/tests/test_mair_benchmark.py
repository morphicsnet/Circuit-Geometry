from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

pytest.importorskip("blt")
pytest.importorskip("mair")

from blt.export import run_analysis, run_trace
from geoclt.adapters.capabilities import hybrid_blt_capabilities
from geoclt.profiles import BenchmarkLaneConfig
from geoclt.workspace import Workspace


def test_hybrid_blt_capability_profile() -> None:
    caps = hybrid_blt_capabilities().as_dict()
    assert caps["adapter_id"] == "blt_hybrid_qwen"
    assert caps["block_granularity"] == "hybrid-3:1"


def test_run_mair_benchmark_from_manifest(tmp_path: Path) -> None:
    manifest_path = run_trace("Geo consumes BLT artifacts.", "trace-geo-1", tmp_path / "trace", backend="mock")
    manifest_path = run_analysis(manifest_path)
    ws = Workspace.create(tmp_path / "workspace")
    result = ws.run_mair_benchmark(
        manifest_path,
        BenchmarkLaneConfig(lane_id="mair-assurance.v1", behavior_id="mechanistic_assurance"),
    )
    assert result["trace_id"] == "trace-geo-1"
    assert Path(result["artifacts"]["assurance_receipt"]).exists()
    assert "decision_receipt" in result
