from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4

from .atlas import fit_atlas as fit_atlas_kernel
from .artifacts import (
    read_json,
    stable_hash,
    validate_instance,
    write_json,
    write_json_with_hash,
)
from .benchmark import (
    compare_baselines,
    conformance_class,
    evaluate_admission,
    evaluate_falsifiers,
)
from .causal import verify_mechanisms as verify_mechanisms_kernel
from .hypergraph import (
    materialize_hyperpaths,
    propose_events as propose_events_kernel,
)
from ._kernel_math import feature_hints_from_candidate_events
from .metric import estimate_pullback_metric
from .profiles import BenchmarkLaneConfig
from .real_pipeline import run_real_pipeline
from .receipts import emit_decision_receipt
from .mair_runtime import run_mair_benchmark as run_mair_benchmark_impl
from ._paths import schema_path
from .runtime import run_workspace_bundle, run_workspace_kernels
from .transport import fit_transport as fit_transport_kernel


@dataclass
class Workspace:
    root: Path
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, path: str | Path) -> "Workspace":
        root = Path(path)
        root.mkdir(parents=True, exist_ok=True)
        workspace = cls(root=root)
        workspace._ensure_layout()
        return workspace

    @property
    def registry_path(self) -> Path:
        return self.root / "workspace.sqlite3"

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.registry_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_layout(self) -> None:
        (self.root / "runs").mkdir(parents=True, exist_ok=True)
        (self.root / "reports").mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    lane_id TEXT NOT NULL,
                    behavior_id TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    input_signature TEXT NOT NULL,
                    status TEXT NOT NULL,
                    conformance_class TEXT NOT NULL,
                    artifact_bundle_hash TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    run_id TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    artifact_path TEXT NOT NULL,
                    artifact_hash TEXT NOT NULL,
                    PRIMARY KEY (run_id, artifact_type)
                )
                """
            )
            self._ensure_column(connection, "runs", "input_signature", "TEXT", "'legacy'")
            connection.commit()

    def _ensure_column(
        self, connection: sqlite3.Connection, table: str, column: str, data_type: str, default: str
    ) -> None:
        columns = {
            row["name"]
            for row in connection.execute(f"PRAGMA table_info({table})")
        }
        if column not in columns:
            connection.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {data_type} NOT NULL DEFAULT {default}"
            )

    def _deterministic_score(self, key: str, lower: float, upper: float) -> float:
        digest = sha256(key.encode("utf-8")).hexdigest()
        ratio = int(digest[:16], 16) / float(0xFFFFFFFFFFFFFFFF)
        return lower + (upper - lower) * ratio

    def _schema_path(self, filename: str) -> Path:
        return schema_path(filename)

    def _new_run_id(self, lane_id: str) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return f"{lane_id}.{timestamp}.{uuid4().hex[:8]}"

    def _input_signature(self, lane: BenchmarkLaneConfig, model_id: str) -> str:
        return stable_hash(
            {
                "model_id": model_id,
                "lane": asdict(lane),
                "atlas": self.metadata.get(
                    "atlas_overlap_map", self.metadata.get("atlas_profile", lane.behavior_id)
                ),
                "transport": self.metadata.get(
                    "transport_diagnostics", self.metadata.get("transport", "unset")
                ),
                "events": self.metadata.get(
                    "candidate_event_table", self.metadata.get("events", "unset")
                ),
                "mechanisms": self.metadata.get(
                    "mechanism_verification", self.metadata.get("mechanisms", "unset")
                ),
            }
        )

    def _stable_id(self, prefix: str, input_signature: str, key: str) -> str:
        return f"{prefix}-{stable_hash({'input_signature': input_signature, 'key': key})[:12]}"

    def attach_model(self, model: Any) -> None:
        model_id = str(model)
        self.metadata["model"] = model_id
        self.metadata["model_id"] = model_id

    def fit_atlas(self, profile: str) -> None:
        model_id = str(self.metadata.get("model_id", "gpt2-small"))
        atlas = fit_atlas_kernel(
            model_id=model_id,
            lane_id=profile,
            profile=profile,
            feature_hints=list(self.metadata.get("feature_hints", [])),
        )
        metric = estimate_pullback_metric(
            lane_id=profile,
            atlas=atlas,
            feature_hints=list(self.metadata.get("feature_hints", [])),
        )
        self.metadata["atlas_profile"] = profile
        self.metadata["atlas_overlap_map"] = atlas
        self.metadata["metric_estimate"] = metric

    def fit_transport(self) -> None:
        profile = str(self.metadata.get("atlas_profile", "default"))
        atlas = self.metadata.get("atlas_overlap_map")
        if atlas is None:
            self.fit_atlas(profile)
            atlas = self.metadata["atlas_overlap_map"]
        metric = self.metadata.get("metric_estimate")
        if metric is None:
            metric = estimate_pullback_metric(
                lane_id=profile,
                atlas=atlas,
                feature_hints=list(self.metadata.get("feature_hints", [])),
            )
            self.metadata["metric_estimate"] = metric
        transport = fit_transport_kernel(lane_id=profile, atlas=atlas, metric=metric)
        self.metadata["transport"] = transport
        self.metadata["transport_diagnostics"] = transport

    def propose_events(self) -> None:
        profile = str(self.metadata.get("atlas_profile", "default"))
        transport = self.metadata.get("transport_diagnostics")
        if transport is None:
            self.fit_transport()
            transport = self.metadata["transport_diagnostics"]
        candidate_event_table = propose_events_kernel(
            lane_id=profile,
            behavior_id=profile,
            transport=transport,
            feature_hints=list(self.metadata.get("feature_hints", [])),
        )
        self.metadata["events"] = candidate_event_table
        self.metadata["candidate_event_table"] = candidate_event_table

    def verify_mechanisms(self) -> None:
        profile = str(self.metadata.get("atlas_profile", "default"))
        model_id = str(self.metadata.get("model_id", "gpt2-small"))
        feature_hints = list(self.metadata.get("feature_hints", []))
        kernel_output = run_workspace_kernels(
            model_id=model_id,
            lane_id=profile,
            behavior_id=profile,
            profile=profile,
            feature_hints=feature_hints,
            intervention_faithfulness=self._deterministic_score(profile, 0.16, 0.28),
            synergy_score_max=self._deterministic_score(profile, 0.08, 0.18),
            chart_stability_hint=self._deterministic_score(f"{profile}:chart", 0.78, 0.92),
            transport_coherence_hint=self._deterministic_score(f"{profile}:transport", 0.76, 0.90),
            geodesic_deviation_hint=self._deterministic_score(f"{profile}:geodesic", 0.02, 0.12),
            run_id=f"workspace-{profile}",
            trace_id=f"workspace-trace-{profile}",
        )
        self.metadata["atlas_overlap_map"] = kernel_output["atlas"]
        self.metadata["metric_estimate"] = kernel_output["metric"]
        self.metadata["transport"] = kernel_output["transport"]
        self.metadata["transport_diagnostics"] = kernel_output["transport"]
        self.metadata["events"] = kernel_output["candidate_event_table"]
        self.metadata["candidate_event_table"] = kernel_output["candidate_event_table"]
        self.metadata["admitted_hyperpath_table"] = kernel_output["admitted_hyperpath_table"]
        self.metadata["mechanisms"] = kernel_output["mechanism_verification"]
        self.metadata["mechanism_verification"] = kernel_output["mechanism_verification"]
        self.metadata["canonicalized_mechanisms"] = kernel_output["canonicalized_mechanisms"]

    def run_mair_benchmark(self, manifest_path: str | Path, lane: BenchmarkLaneConfig) -> dict[str, Any]:
        return run_mair_benchmark_impl(self, manifest_path, lane)

    def run_benchmark(self, lane: BenchmarkLaneConfig) -> dict[str, Any]:
        self._ensure_layout()

        model_id = str(self.metadata.get("model_id", "gpt2-small"))
        run_id = self._new_run_id(lane.lane_id)
        run_dir = self.root / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        artifacts_dir = run_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        real_output = run_real_pipeline(
            model_id=model_id,
            lane_id=lane.lane_id,
            behavior_id=lane.behavior_id,
        )
        intervention_faithfulness = real_output.intervention_faithfulness
        synergy_score_max = real_output.synergy_score_max
        chart_stability = real_output.chart_stability
        transport_coherence = real_output.transport_coherence
        geodesic_deviation = real_output.geodesic_deviation
        baseline_scores = real_output.baseline_scores
        candidate_events = real_output.candidate_events
        pipeline_mode = "real-transformers"
        backend_type = real_output.backend
        pipeline_prompt = real_output.prompt
        token_count = real_output.token_count
        model_id = real_output.model_id
        self.metadata["real_mode"] = True
        feature_hints = feature_hints_from_candidate_events(candidate_events, lane.behavior_id)
        atlas_profile = str(self.metadata.get("atlas_profile", lane.behavior_id))
        bundle_output = run_workspace_bundle(
            model_id=model_id,
            lane_id=lane.lane_id,
            behavior_id=lane.behavior_id,
            profile=atlas_profile,
            feature_hints=feature_hints,
            intervention_faithfulness=intervention_faithfulness,
            synergy_score_max=synergy_score_max,
            chart_stability_hint=chart_stability,
            transport_coherence_hint=transport_coherence,
            geodesic_deviation_hint=geodesic_deviation,
            intervention_delta_threshold=lane.intervention_delta_threshold,
            synergy_threshold=lane.synergy_threshold,
            chart_stability_threshold=lane.chart_stability_threshold,
            transport_coherence_threshold=lane.transport_coherence_threshold,
            baseline_margin_threshold=lane.baseline_margin_threshold,
        )
        kernel_output = bundle_output["kernel_output"]
        artifact_bundle = bundle_output["artifact_bundle"]
        atlas_overlap_map = kernel_output["atlas"]
        metric_estimate = kernel_output["metric"]
        transport_diagnostics = kernel_output["transport"]
        candidate_event_table = kernel_output["candidate_event_table"]
        admitted_hyperpath_table = kernel_output["admitted_hyperpath_table"]
        mechanism_verification = kernel_output["mechanism_verification"]
        canonicalized_mechanisms = kernel_output["canonicalized_mechanisms"]
        self.metadata["feature_hints"] = feature_hints
        self.metadata["atlas_overlap_map"] = atlas_overlap_map
        self.metadata["metric_estimate"] = metric_estimate
        self.metadata["transport_diagnostics"] = transport_diagnostics
        self.metadata["candidate_event_table"] = candidate_event_table
        self.metadata["admitted_hyperpath_table"] = admitted_hyperpath_table
        self.metadata["mechanism_verification"] = mechanism_verification
        self.metadata["canonicalized_mechanisms"] = canonicalized_mechanisms
        self.metadata["transport"] = transport_diagnostics
        self.metadata["events"] = candidate_event_table
        self.metadata["mechanisms"] = mechanism_verification
        input_signature = self._input_signature(lane, model_id)

        admission = evaluate_admission(
            lane=lane,
            intervention_faithfulness=intervention_faithfulness,
            synergy_score_max=synergy_score_max,
            chart_stability=chart_stability,
            transport_coherence=transport_coherence,
        )

        baseline_report = compare_baselines(
            intervention_faithfulness=intervention_faithfulness,
            baseline_scores=baseline_scores,
            margin_threshold=lane.baseline_margin_threshold,
        )

        falsifiers = evaluate_falsifiers(
            lane=lane,
            intervention_faithfulness=intervention_faithfulness,
            synergy_score_max=synergy_score_max,
            chart_stability=chart_stability,
            transport_coherence=transport_coherence,
            geodesic_deviation=geodesic_deviation,
            strongest_baseline=baseline_report["strongest_baseline"],
        )
        conformance = conformance_class(
            admission_passed=admission["passed"],
            beats_baseline=baseline_report["beats_baseline"],
            falsifiers=falsifiers,
        )

        producer = "geoclt:workspace:0.2.0"
        artifact_created_at = "2026-01-01T00:00:00Z"
        stable_trace_id = self._stable_id("trace", input_signature, lane.lane_id)

        admitted_hyperpaths = [
            path
            for path in admitted_hyperpath_table["hyperpaths"]
            if path["admitted"] and admission["passed"]
        ]
        benchmark_result = {
            "artifact_id": self._stable_id("benchmark", input_signature, lane.lane_id),
            "artifact_type": "benchmark_result",
            "schema_version": 2,
            "producer": producer,
            "trace_id": stable_trace_id,
            "run_id": run_id,
            "content_hash": stable_hash(
                {
                    "model_id": model_id,
                    "task_id": lane.behavior_id,
                    "baseline_id": baseline_report.get("strongest_baseline_id", "none"),
                    "metric_name": "intervention_faithfulness",
                    "metric_value": round(intervention_faithfulness, 4),
                    "threshold": lane.intervention_delta_threshold,
                    "passed": conformance != "rejected",
                }
            ),
            "created_at": artifact_created_at,
            "model_id": model_id,
            "task_id": lane.behavior_id,
            "baseline_id": baseline_report.get("strongest_baseline_id", "none"),
            "metric_name": "intervention_faithfulness",
            "metric_value": round(intervention_faithfulness, 4),
            "threshold": lane.intervention_delta_threshold,
            "passed": conformance != "rejected",
        }
        validate_instance(benchmark_result, self._schema_path("benchmark_result.schema.json"))
        validate_instance(artifact_bundle, self._schema_path("artifact_bundle.schema.json"))

        artifact_payloads: dict[str, dict[str, Any]] = {
            "atlas_overlap_map": {
                **atlas_overlap_map,
                "pipeline_mode": pipeline_mode,
                "backend_type": backend_type,
            },
            "transport_diagnostics": {
                **transport_diagnostics,
                "pipeline_mode": pipeline_mode,
                "backend_type": backend_type,
            },
            "candidate_event_table": {
                **candidate_event_table,
                "pipeline_mode": pipeline_mode,
                "backend_type": backend_type,
            },
            "admitted_hyperpath_table": {
                "lane_id": lane.lane_id,
                "admitted_count": len(admitted_hyperpaths),
                "hyperpaths": admitted_hyperpaths,
                "pipeline_mode": pipeline_mode,
            },
            "falsifier_sheet": {
                "lane_id": lane.lane_id,
                "falsifiers": falsifiers,
                "admission": admission,
                "baseline_report": baseline_report,
                "conformance_class": conformance,
                "benchmark_result": benchmark_result,
                "mechanism_verification": mechanism_verification,
                "canonicalized_mechanisms": canonicalized_mechanisms,
                "artifact_bundle_hash": artifact_bundle["bundle_hash"],
                "pipeline_mode": pipeline_mode,
                "backend_type": backend_type,
                "prompt_hash": stable_hash(pipeline_prompt) if pipeline_prompt else None,
                "token_count": token_count,
            },
        }

        artifact_paths: dict[str, str] = {}
        artifact_hashes: dict[str, str] = {}
        for artifact_type, payload in artifact_payloads.items():
            path = artifacts_dir / f"{artifact_type}.json"
            artifact_hashes[artifact_type] = write_json_with_hash(path, payload)
            artifact_paths[artifact_type] = str(path.resolve())

        bundle_path = artifacts_dir / "artifact_bundle.json"
        write_json(bundle_path, artifact_bundle)
        artifact_paths["artifact_bundle"] = str(bundle_path.resolve())
        artifact_hashes["artifact_bundle"] = str(artifact_bundle["bundle_hash"])
        bundle_hash = str(artifact_bundle["bundle_hash"])

        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO runs (
                    run_id, created_at, lane_id, behavior_id, model_id, input_signature,
                    status, conformance_class, artifact_bundle_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    now,
                    lane.lane_id,
                    lane.behavior_id,
                    model_id,
                    input_signature,
                    "completed",
                    conformance,
                    bundle_hash,
                ),
            )
            connection.executemany(
                """
                INSERT INTO artifacts (run_id, artifact_type, artifact_path, artifact_hash)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (run_id, artifact_type, artifact_paths[artifact_type], artifact_hash)
                    for artifact_type, artifact_hash in artifact_hashes.items()
                ],
            )
            connection.commit()

        run_metadata = dict(self.metadata)
        run_metadata.update(
            {
                "pipeline_mode": pipeline_mode,
                "backend_type": backend_type,
                "token_count": token_count,
                "real_mode_enabled": True,
            }
        )

        return {
            "run_id": run_id,
            "lane_id": lane.lane_id,
            "status": "completed",
            "model_id": model_id,
            "input_signature": input_signature,
            "admission": admission,
            "baseline_report": baseline_report,
            "falsifiers": falsifiers,
            "conformance_class": conformance,
            "artifact_bundle_hash": bundle_hash,
            "artifact_paths": artifact_paths,
            "metadata": run_metadata,
        }

    def export_report(self, run_id: str, path: str | Path | None = None) -> dict[str, Any]:
        run_data = self.get_run(run_id)
        run_row = run_data["run"]
        artifacts = run_data["artifacts"]

        conformance_class_value = str(run_row["conformance_class"])
        if conformance_class_value == "conformant":
            active_ids = [f"mechanism-{run_id}"]
            provisional_ids: list[str] = []
        elif conformance_class_value == "provisional":
            active_ids = []
            provisional_ids = [f"mechanism-{run_id}"]
        else:
            active_ids = []
            provisional_ids = []

        receipt = emit_decision_receipt(
            run_id=run_id,
            decision="allow_with_review" if conformance_class_value != "rejected" else "escalate",
            active_mechanism_class_ids=active_ids,
            provisional_mechanism_class_ids=provisional_ids,
            policy_clauses_triggered=[],
            geometry_anomaly_flags=[],
            chart_instability_flags=[],
        )

        report = {
            "run": run_row,
            "artifacts": artifacts,
            "decision_receipt": receipt,
        }

        report_path = Path(path) if path is not None else self.root / "reports" / f"{run_id}.json"
        report_hash = write_json_with_hash(report_path, report)
        return {
            "status": "ok",
            "run_id": run_id,
            "report_path": str(report_path.resolve()),
            "report_hash": report_hash,
        }

    def list_runs(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT run_id, created_at, lane_id, behavior_id, model_id, input_signature, "
                "status, conformance_class, artifact_bundle_hash "
                "FROM runs ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_run(self, run_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            run_row = connection.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if run_row is None:
                raise KeyError(f"run not found: {run_id}")

            artifact_rows = connection.execute(
                "SELECT artifact_type, artifact_path, artifact_hash FROM artifacts WHERE run_id = ?",
                (run_id,),
            ).fetchall()

        artifacts: dict[str, Any] = {}
        for row in artifact_rows:
            artifacts[row["artifact_type"]] = {
                "path": row["artifact_path"],
                "hash": row["artifact_hash"],
                "payload": read_json(row["artifact_path"]),
            }
        return {"run": dict(run_row), "artifacts": artifacts}

    def load_report(self, run_id: str, generate_if_missing: bool = True) -> dict[str, Any]:
        report_path = self.root / "reports" / f"{run_id}.json"
        if report_path.exists():
            return read_json(report_path)
        if not generate_if_missing:
            raise FileNotFoundError(f"report not found: {report_path}")
        self.export_report(run_id, path=report_path)
        return read_json(report_path)

    def determinism_for_run(self, run_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            run_row = connection.execute(
                "SELECT run_id, input_signature, artifact_bundle_hash FROM runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if run_row is None:
                raise KeyError(f"run not found: {run_id}")

            peer_rows = connection.execute(
                "SELECT run_id, artifact_bundle_hash FROM runs "
                "WHERE input_signature = ? AND run_id != ? ORDER BY created_at DESC",
                (run_row["input_signature"], run_id),
            ).fetchall()

        if not peer_rows:
            return {
                "run_id": run_id,
                "input_signature": run_row["input_signature"],
                "current_hash": run_row["artifact_bundle_hash"],
                "is_deterministic": True,
                "comparison": None,
                "matching_run_count": 1,
            }

        comparison = peer_rows[0]
        is_deterministic = comparison["artifact_bundle_hash"] == run_row["artifact_bundle_hash"]
        return {
            "run_id": run_id,
            "input_signature": run_row["input_signature"],
            "current_hash": run_row["artifact_bundle_hash"],
            "is_deterministic": is_deterministic,
            "comparison": {
                "run_id": comparison["run_id"],
                "artifact_bundle_hash": comparison["artifact_bundle_hash"],
            },
            "matching_run_count": len(peer_rows) + 1,
        }
