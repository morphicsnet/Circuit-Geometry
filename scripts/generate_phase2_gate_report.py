from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SRC = REPO_ROOT / "python"
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from geoclt.adapters import LlamaCppAdapter, MockAdapter, TransformersAdapter, VllmAdapter
from geoclt.artifacts import derive_artifact_id, stable_hash
from geoclt.sidecar import connect_sidecar


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def main() -> int:
    registry = json.loads((REPO_ROOT / "schemas" / "registry.json").read_text(encoding="utf-8"))
    artifacts_registry = registry["artifacts"]

    compatibility_checks: dict[str, dict[str, bool]] = {}
    for artifact_type, policy in artifacts_registry.items():
        current = policy["current_version"]
        minimum = policy["min_compatible_version"]
        n_minus_1_ok = (current - 1) >= minimum if current > 1 else True
        compatibility_checks[artifact_type] = {
            "n": current >= minimum,
            "n_minus_1": n_minus_1_ok,
            "n_minus_2_rejected": (current - 2) < minimum,
        }

    adapter = MockAdapter("gpt2-small")
    real_adapters = [
        TransformersAdapter("gpt2-small"),
        VllmAdapter("gpt2-small"),
        LlamaCppAdapter("gpt2-small"),
    ]
    sidecar = connect_sidecar()
    result = sidecar.stream_trace(
        trace_id="phase2-trace",
        adapter_id=adapter.capabilities().adapter_id,
        model_id="gpt2-small",
        lane_id="factual_retrieval.v1",
        run_id="phase2-run",
        chunks=[b"a", b"b", b"c"],
    )
    repeat_result = sidecar.stream_trace(
        trace_id="phase2-trace",
        adapter_id=adapter.capabilities().adapter_id,
        model_id="gpt2-small",
        lane_id="factual_retrieval.v1",
        run_id="phase2-run",
        chunks=[b"a", b"b", b"c"],
    )

    prompt = "what is the capital of france"
    tokens_before = adapter.infer_tokens(prompt)
    logits_before = adapter.infer_logits_hash(prompt)
    adapter.install_passive_hooks()
    tokens_after = adapter.infer_tokens(prompt)
    logits_after = adapter.infer_logits_hash(prompt)
    adapter.remove_hooks()

    # Canonical serialization stability checks.
    canonical_hash_one = stable_hash({"z": 1, "a": [1, 2, 3]})
    canonical_hash_two = stable_hash({"a": [1, 2, 3], "z": 1})
    deterministic_artifact_id = (
        derive_artifact_id("event_record", 2, "a" * 64)
        == derive_artifact_id("event_record", 2, "a" * 64)
    )

    # Duplicate chunk conflict hard gate.
    conflict_sidecar = connect_sidecar()
    conflict_sidecar.start_trace(
        trace_id="phase2-trace-conflict",
        adapter_id=adapter.capabilities().adapter_id,
        model_id="gpt2-small",
        lane_id="factual_retrieval.v1",
        run_id="phase2-run-conflict",
    )
    conflict_sidecar.stream_activation_chunk(
        trace_id="phase2-trace-conflict",
        chunk_idempotency_key="dup-key",
        payload=b"same",
        layer_id=1,
        sequence_no=1,
    )
    duplicate_noop = conflict_sidecar.stream_activation_chunk(
        trace_id="phase2-trace-conflict",
        chunk_idempotency_key="dup-key",
        payload=b"same",
        layer_id=1,
        sequence_no=1,
    )
    duplicate_conflict = conflict_sidecar.stream_activation_chunk(
        trace_id="phase2-trace-conflict",
        chunk_idempotency_key="dup-key",
        payload=b"different",
        layer_id=1,
        sequence_no=1,
    )

    adapter_checks: list[dict[str, Any]] = []
    for real in real_adapters:
        caps = real.capabilities()
        blocks = real.list_blocks()
        tagged = real.tokenize_with_tags("phase two adapter check")
        activations = real.capture_activations("phase two adapter check", blocks[:2])
        adapter_checks.append(
            {
                "adapter_id": caps.adapter_id,
                "capabilities_valid": bool(caps.supported_runtimes) and bool(caps.block_granularity),
                "block_listing_nonempty": bool(blocks),
                "token_tagging_stable": tagged[-1]["tag"] == "answer-token",
                "activation_capture_nonempty": len(activations["activations"]) == 2,
            }
        )

    real_adapter_conformance = all(
        check["capabilities_valid"]
        and check["block_listing_nonempty"]
        and check["token_tagging_stable"]
        and check["activation_capture_nonempty"]
        for check in adapter_checks
    )

    report: dict[str, Any] = {
        "git_commit": _git_commit(),
        "schema_registry_version": registry["version"],
        "adapters_tested": [
            adapter.capabilities().as_dict(),
            *(real.capabilities().as_dict() for real in real_adapters),
        ],
        "mock_roundtrip": bool(result.get("ok", False)),
        "real_adapter_conformance": real_adapter_conformance,
        "adapter_conformance_checks": adapter_checks,
        "passive_non_perturbation": {
            "token_parity": tokens_before == tokens_after,
            "logits_hash_parity": logits_before == logits_after,
        },
        "canonical_serialization": {
            "stable_hash_key_order_invariant": canonical_hash_one == canonical_hash_two,
            "artifact_id_deterministic": deterministic_artifact_id,
        },
        "compatibility_matrix": {
            "policy": registry["compatibility_policy"],
            "checks": compatibility_checks,
        },
        "duplicate_chunk_policy": {
            "duplicate_noop_ok": duplicate_noop.get("ok", False)
            and duplicate_noop.get("message") == "duplicate-noop",
            "conflict_hard_fail": not duplicate_conflict.get("ok", True),
        },
        "determinism": {
            "bundle_hash_present": bool(result.get("bundle", {}).get("bundle_hash")),
            "immutable": bool(result.get("bundle", {}).get("immutable", False)),
            "stable_bundle_hash": result.get("bundle", {}).get("bundle_hash")
            == repeat_result.get("bundle", {}).get("bundle_hash"),
        },
        "sidecar_roundtrip_status": result,
    }

    report["overall_pass"] = (
        registry["compatibility_policy"] == "strict_n_n_minus_1"
        and report["mock_roundtrip"]
        and report["real_adapter_conformance"]
        and report["passive_non_perturbation"]["token_parity"]
        and report["passive_non_perturbation"]["logits_hash_parity"]
        and report["canonical_serialization"]["stable_hash_key_order_invariant"]
        and report["canonical_serialization"]["artifact_id_deterministic"]
        and report["determinism"]["immutable"]
        and report["determinism"]["stable_bundle_hash"]
        and report["duplicate_chunk_policy"]["duplicate_noop_ok"]
        and report["duplicate_chunk_policy"]["conflict_hard_fail"]
        and all(
            check["n"] and check["n_minus_1"] and check["n_minus_2_rejected"]
            for check in compatibility_checks.values()
        )
    )

    output = REPO_ROOT / "outputs" / "phase2_gate_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
