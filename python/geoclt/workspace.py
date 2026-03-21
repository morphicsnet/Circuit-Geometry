from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4

from .artifacts import (
    content_hash,
    derive_artifact_id,
    read_json,
    stable_hash,
    validate_instance,
    validate_instances,
    write_json_with_hash,
)
from .benchmark import (
    compare_baselines,
    conformance_class,
    evaluate_admission,
    evaluate_falsifiers,
)
from .profiles import BenchmarkLaneConfig
from .real_pipeline import run_real_pipeline
from .receipts import emit_decision_receipt


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
        return Path(__file__).resolve().parents[2] / "schemas" / filename

    def _new_run_id(self, lane_id: str) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return f"{lane_id}.{timestamp}.{uuid4().hex[:8]}"

    def _input_signature(self, lane: BenchmarkLaneConfig, model_id: str) -> str:
        return stable_hash(
            {
                "model_id": model_id,
                "lane": asdict(lane),
                "atlas_profile": self.metadata.get("atlas_profile", lane.behavior_id),
                "transport": self.metadata.get("transport", "unset"),
                "events": self.metadata.get("events", "unset"),
                "mechanisms": self.metadata.get("mechanisms", "unset"),
            }
        )

    def _stable_id(self, prefix: str, input_signature: str, key: str) -> str:
        return f"{prefix}-{stable_hash({'input_signature': input_signature, 'key': key})[:12]}"

    def attach_model(self, model: Any) -> None:
        model_id = str(model)
        self.metadata["model"] = model_id
        self.metadata["model_id"] = model_id

    def fit_atlas(self, profile: str) -> None:
        self.metadata["atlas_profile"] = profile

    def fit_transport(self) -> None:
        self.metadata["transport"] = "fit"

    def propose_events(self) -> None:
        self.metadata["events"] = "proposed"

    def verify_mechanisms(self) -> None:
        self.metadata["mechanisms"] = "verified"

    def run_benchmark(self, lane: BenchmarkLaneConfig) -> dict[str, Any]:
        self._ensure_layout()

        model_id = str(self.metadata.get("model_id", "gpt2-small"))
        input_signature = self._input_signature(lane, model_id)
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

        def enrich_record(record: dict[str, Any], artifact_type: str) -> dict[str, Any]:
            digest = content_hash(record)
            return {
                "artifact_id": derive_artifact_id(artifact_type, 2, digest),
                "artifact_type": artifact_type,
                "schema_version": 2,
                "producer": producer,
                "trace_id": stable_trace_id,
                "run_id": run_id,
                "content_hash": digest,
                "created_at": artifact_created_at,
                **record,
            }

        admitted_hyperpaths: list[dict[str, Any]] = []
        if admission["passed"]:
            admitted_hyperpaths.append(
                {
                    "path_id": self._stable_id("path", input_signature, "1"),
                    "behavior_id": lane.behavior_id,
                    "event_ids": [event["event_id"] for event in candidate_events],
                    "layer_ids": [5, 6],
                    "chart_stability": round(chart_stability, 4),
                    "transport_coherence": round(transport_coherence, 4),
                    "intervention_faithfulness": round(intervention_faithfulness, 4),
                    "synergy_score_max": round(synergy_score_max, 4),
                    "geodesic_deviation": round(geodesic_deviation, 4),
                    "admitted": conformance != "rejected",
                }
            )

        event_records = [
            enrich_record(
                {
                    "event_id": event["event_id"],
                    "sample_id": self._stable_id("sample", input_signature, "1"),
                    "layer_span": [5, 6],
                "time_window": "answer-token",
                "participant_set": event["participant_set"],
                "participant_types": event["participant_types"],
                "transport_context_id": "context-default",
                    "causal_weight": event["causal_weight"],
                    "reliability_score": event["reliability_score"],
                    "proposer_score": None,
                },
                "event_record",
            )
            for event in candidate_events
        ]
        validate_instances(event_records, self._schema_path("event_record.schema.json"))

        hyperpath_records = [
            enrich_record(
                {
                "path_id": path["path_id"],
                "behavior_id": path["behavior_id"],
                "event_ids": path["event_ids"],
                "chart_ids": ["chart-a", "chart-b"],
                "layer_ids": path["layer_ids"],
                "transport_edge_ids": ["edge-1"],
                "geodesic_deviation": path["geodesic_deviation"],
                "chart_stability": path["chart_stability"],
                "transport_coherence": path["transport_coherence"],
                "intervention_faithfulness": path["intervention_faithfulness"],
                "synergy_score_max": path["synergy_score_max"],
                "admitted": bool(path["admitted"]),
                },
                "hyperpath_record",
            )
            for path in admitted_hyperpaths
        ]
        validate_instances(hyperpath_records, self._schema_path("hyperpath_record.schema.json"))

        benchmark_result = enrich_record(
            {
            "run_id": self._stable_id("benchmark", input_signature, lane.lane_id),
            "model_id": model_id,
            "task_id": lane.behavior_id,
            "baseline_id": baseline_report.get("strongest_baseline_id", "none"),
            "metric_name": "intervention_faithfulness",
            "metric_value": round(intervention_faithfulness, 4),
            "threshold": lane.intervention_delta_threshold,
            "passed": conformance != "rejected",
            },
            "benchmark_result",
        )
        validate_instance(benchmark_result, self._schema_path("benchmark_result.schema.json"))

        artifact_payloads: dict[str, dict[str, Any]] = {
            "atlas_overlap_map": {
                "model_id": model_id,
                "lane_id": lane.lane_id,
                "chart_count": 4,
                "overlap_score": round(chart_stability, 4),
                "profile": self.metadata.get("atlas_profile", lane.behavior_id),
                "pipeline_mode": pipeline_mode,
                "backend_type": backend_type,
            },
            "transport_diagnostics": {
                "lane_id": lane.lane_id,
                "loop_consistency": round(transport_coherence, 4),
                "distortion": round(max(0.0, 1.0 - transport_coherence), 4),
                "coherence": round(transport_coherence, 4),
                "geodesic_deviation": round(geodesic_deviation, 4),
                "pipeline_mode": pipeline_mode,
                "backend_type": backend_type,
            },
            "candidate_event_table": {
                "lane_id": lane.lane_id,
                "candidate_count": len(candidate_events),
                "events": candidate_events,
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

        bundle_hash = stable_hash(
            {
                "input_signature": input_signature,
                "lane_id": lane.lane_id,
                "model_id": model_id,
                "artifact_hashes": artifact_hashes,
            }
        )

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
