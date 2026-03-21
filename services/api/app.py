from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import os
import sys
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_SRC = REPO_ROOT / "python"
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from geoclt import BenchmarkLaneConfig, Workspace
from geoclt.artifacts import (
    read_json,
    stable_hash,
    validate_instance,
    write_json,
)
from geoclt.demo import (
    build_run_config_record,
    deterministic_replay,
    load_manifest,
    run_demo_lane,
)
from geoclt.differential import cohort_summary, diff_mechanism_sets
from geoclt.external_services import queue_event, queue_backend, store_backend, store_bundle
from geoclt.field_trials import (
    build_operator_review_record,
    build_pilot_metrics_bundle,
    build_pilot_run_record,
    build_pilot_scope_policy_record,
    build_drift_alert_record,
    compute_drift_metric,
    compute_trust_metrics,
    scope_decision,
)
from geoclt.models import (
    DEFAULT_PHI_PROFILE,
    DEFAULT_QWEN_PROFILE,
    PhiRunner,
    QwenRunner,
    profile_frozen,
)
from geoclt.reports import build_analysis_report_bundle

ALLOWED_POLICY_ACTIONS = {
    "allow",
    "allow_with_review",
    "route_to_fallback",
    "block",
    "escalate",
}

DEMO_LANE_ASSET_DIRS = {
    "realworld-claims-triage.v1": "claims",
    "realworld-policy-qa.v1": "policy",
    "realworld-structured-intake.v1": "intake",
}

MODEL_RUNNERS = {
    DEFAULT_QWEN_PROFILE.model_profile_id: QwenRunner,
    DEFAULT_PHI_PROFILE.model_profile_id: PhiRunner,
}

app = FastAPI(title="Geo-CLT API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _auth_mode() -> str:
    return os.getenv("GEOCLT_AUTH_MODE", "token").strip().lower()


def _auth_token() -> str:
    return os.getenv("GEOCLT_AUTH_TOKEN", "geoclt-local-token")


def require_auth_token(authorization: str | None = Header(default=None)) -> str:
    if _auth_mode() != "token":
        return "auth-disabled"
    expected = f"Bearer {_auth_token()}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="unauthorized")
    return "token-authenticated"


class RunRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    workspace: str = Field(default="runs/factual-retrieval", min_length=1)
    lane_id: str = Field(default="factual_retrieval.v1")
    behavior_id: str = Field(default="factual_retrieval")
    model_id: str = Field(default="gpt2-small")
    atlas_profile: str = Field(default="factual_retrieval")
    fit_transport: bool = True
    propose_events: bool = True
    verify_mechanisms: bool = True


class TraceRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    workspace: str = Field(default="runs/factual-retrieval", min_length=1)
    lane_id: str = Field(default="claims-triage.v1")
    behavior_id: str = Field(default="factual_retrieval")
    model_id: str = Field(default="gpt2-small")


class EvaluateLaneRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    workspace: str = Field(default="runs/factual-retrieval", min_length=1)
    run_id: str = Field(min_length=1)
    lane_id: str = Field(default="claims-triage.v1")


class DemoSubmitRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    workspace: str = Field(default="runs/phase4-demo", min_length=1)
    lane_id: str = Field(default="realworld-claims-triage.v1")
    model_profile_id: str = Field(default=DEFAULT_QWEN_PROFILE.model_profile_id)
    requested_action: str = Field(default="allow")
    force_fallback: bool = False


class PilotSubmitRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    workspace: str = Field(default="runs/phase4-demo", min_length=1)
    lane_id: str = Field(default="realworld-claims-triage.v1")
    user_id: str = Field(default="demo-user")
    task: str = Field(default="claims-triage")
    corpus: str = Field(default="golden")
    requested_action: str = Field(default="allow")
    demo_run_id: str | None = None


class PilotReviewRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    workspace: str = Field(default="runs/phase4-demo", min_length=1)
    pilot_run_id: str = Field(min_length=1)
    reviewer_id: str = Field(min_length=1)
    task_ref: str = Field(default="task-1")
    accepted: bool = True
    override: bool = False
    explanation_usefulness: float = 0.9
    receipt_usefulness: float = 0.9
    escalation_appropriateness: float = 0.9
    confidence_calibration_agreement: float = 0.9


def _utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _workspace_root(workspace: str) -> Path:
    root = Path(workspace)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _phase4_dirs(workspace: str) -> dict[str, Path]:
    root = _workspace_root(workspace) / "phase4"
    mapping = {
        "root": root,
        "demo_runs": root / "demo_runs",
        "demo_receipts": root / "demo_receipts",
        "demo_reports": root / "demo_reports",
        "pilot_runs": root / "pilot_runs",
        "pilot_reviews": root / "pilot_reviews",
        "pilot_metrics": root / "pilot_metrics",
        "pilot_scope": root / "pilot_scope",
    }
    for directory in mapping.values():
        directory.mkdir(parents=True, exist_ok=True)
    return mapping


def _lane_asset_paths(lane_id: str) -> tuple[Path, Path]:
    lane_dir = DEMO_LANE_ASSET_DIRS.get(lane_id)
    if lane_dir is None:
        raise HTTPException(status_code=400, detail=f"unsupported demo lane: {lane_id}")
    base = REPO_ROOT / "data" / "golden" / "phase4a" / lane_dir
    return base / "manifest.json", base / "scorecard.json"


def _load_scorecard(path: Path) -> dict[str, Any]:
    scorecard = read_json(path)
    validate_instance(scorecard, REPO_ROOT / "schemas" / "demo_scorecard.schema.json")
    return scorecard


def _runner_for_profile(profile_id: str):
    runner_cls = MODEL_RUNNERS.get(profile_id)
    if runner_cls is None:
        raise HTTPException(status_code=400, detail=f"unsupported model profile: {profile_id}")
    runner = runner_cls()
    if runner.profile.model_profile_id != profile_id:
        raise HTTPException(status_code=400, detail=f"model profile mismatch: {profile_id}")
    return runner


def _next_sequence(directory: Path, prefix: str) -> int:
    return len(list(directory.glob(f"{prefix}*.json"))) + 1


def _load_demo_run(workspace: str, run_id: str) -> dict[str, Any]:
    directories = _phase4_dirs(workspace)
    run_path = directories["demo_runs"] / f"{run_id}.json"
    if not run_path.exists():
        raise HTTPException(status_code=404, detail=f"demo run not found: {run_id}")
    return read_json(run_path)


def _latest_demo_run_for_lane(workspace: str, lane_id: str) -> str | None:
    directories = _phase4_dirs(workspace)
    runs = sorted(directories["demo_runs"].glob("*.json"))
    for path in reversed(runs):
        payload = read_json(path)
        if payload.get("lane_id") == lane_id:
            return payload.get("run_id")
    return None


def _load_or_create_scope_record(workspace: str) -> dict[str, Any]:
    directories = _phase4_dirs(workspace)
    scope_path = directories["pilot_scope"] / "pilot_scope_policy_record.v1.json"
    if scope_path.exists():
        return read_json(scope_path)

    scope_record = build_pilot_scope_policy_record(
        policy_id="pilot-scope",
        policy_version="v1",
        identity_key_id="identity-key-v1",
        in_scope_users=["demo-user", "analyst-1", "analyst-2"],
        in_scope_tasks=["claims-triage", "policy-qa", "structured-intake"],
        allowed_corpora=["golden", "claims-docs", "policy-corpus", "intake-forms"],
        review_required_actions=["allow_with_review", "route_to_fallback", "escalate"],
        prohibited_actions=["autonomous_execute"],
        trace_id="scope-trace-v1",
        run_id="scope-run-v1",
    )
    write_json(scope_path, scope_record)
    return scope_record


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/runs")
def list_runs(workspace: str = Query(..., min_length=1)) -> dict[str, object]:
    ws = Workspace.create(workspace)
    return {"workspace": str(ws.root.resolve()), "runs": ws.list_runs()}


@app.post("/runs")
def create_run(request: RunRequest) -> dict[str, object]:
    ws = Workspace.create(request.workspace)
    ws.attach_model(request.model_id)
    ws.fit_atlas(profile=request.atlas_profile)
    if request.fit_transport:
        ws.fit_transport()
    if request.propose_events:
        ws.propose_events()
    if request.verify_mechanisms:
        ws.verify_mechanisms()
    return ws.run_benchmark(
        BenchmarkLaneConfig(
            lane_id=request.lane_id,
            behavior_id=request.behavior_id,
        )
    )


@app.get("/runs/{run_id}")
def get_run(run_id: str, workspace: str = Query(..., min_length=1)) -> dict[str, object]:
    ws = Workspace.create(workspace)
    try:
        return ws.get_run(run_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/runs/{run_id}/export")
def export_run(run_id: str, workspace: str = Query(..., min_length=1)) -> dict[str, object]:
    ws = Workspace.create(workspace)
    try:
        return ws.export_report(run_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/reports/{run_id}")
def get_report(run_id: str, workspace: str = Query(..., min_length=1)) -> dict[str, object]:
    ws = Workspace.create(workspace)
    try:
        return ws.load_report(run_id, generate_if_missing=False)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/runs/{run_id}/determinism")
def get_determinism(run_id: str, workspace: str = Query(..., min_length=1)) -> dict[str, object]:
    ws = Workspace.create(workspace)
    try:
        return ws.determinism_for_run(run_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/trace")
def create_trace(
    request: TraceRequest,
    _auth: str = Depends(require_auth_token),
) -> dict[str, object]:
    ws = Workspace.create(request.workspace)
    ws.attach_model(request.model_id)
    ws.fit_atlas(profile=request.behavior_id)
    ws.fit_transport()
    ws.propose_events()
    ws.verify_mechanisms()
    run = ws.run_benchmark(
        BenchmarkLaneConfig(
            lane_id=request.lane_id,
            behavior_id=request.behavior_id,
        )
    )
    return {
        "status": "ok",
        "run_id": run["run_id"],
        "trace_id": run["artifact_bundle_hash"][:24],
        "lane_id": request.lane_id,
    }


@app.post("/evaluate_lane")
def evaluate_lane(
    request: EvaluateLaneRequest,
    _auth: str = Depends(require_auth_token),
) -> dict[str, object]:
    ws = Workspace.create(request.workspace)
    run = ws.get_run(request.run_id)
    report = ws.load_report(request.run_id)
    receipt = report["decision_receipt"]
    action = receipt.get("action_selected", receipt.get("decision", "allow_with_review"))
    return {
        "status": "ok",
        "run_id": request.run_id,
        "lane_id": request.lane_id,
        "action": action,
        "conformance_class": run["run"]["conformance_class"],
    }


@app.get("/mechanism/{mechanism_id}")
def get_mechanism(mechanism_id: str, workspace: str = Query(..., min_length=1)) -> dict[str, object]:
    ws = Workspace.create(workspace)
    runs = ws.list_runs()
    hit = next((run for run in runs if run["run_id"].endswith(mechanism_id[-8:])), None)
    return {
        "mechanism_id": mechanism_id,
        "workspace": str(ws.root.resolve()),
        "status": "known" if hit else "unknown",
        "source_run_id": hit["run_id"] if hit else None,
    }


@app.get("/decision_receipt/{receipt_id}")
def get_decision_receipt(
    receipt_id: str,
    workspace: str = Query(..., min_length=1),
    _auth: str = Depends(require_auth_token),
) -> dict[str, object]:
    ws = Workspace.create(workspace)
    for run in ws.list_runs():
        report_path = ws.root / "reports" / f"{run['run_id']}.json"
        if not report_path.exists():
            continue
        report = ws.load_report(run["run_id"], generate_if_missing=False)
        receipt = report.get("decision_receipt", {})
        if receipt.get("receipt_id") == receipt_id:
            return receipt
    raise HTTPException(status_code=404, detail=f"receipt not found: {receipt_id}")


@app.get("/analysis/report")
def get_analysis_report(
    workspace: str = Query(..., min_length=1),
    _auth: str = Depends(require_auth_token),
) -> dict[str, object]:
    ws = Workspace.create(workspace)
    runs = ws.list_runs()
    if len(runs) < 2:
        raise HTTPException(status_code=400, detail="at least two runs required for analysis report")

    first = ws.load_report(runs[0]["run_id"])
    second = ws.load_report(runs[1]["run_id"])
    baseline = [
        {"mechanism_id": f"mechanism:{runs[0]['run_id']}", "mechanism_class_id": "class:a"},
    ]
    candidate = [
        {"mechanism_id": f"mechanism:{runs[1]['run_id']}", "mechanism_class_id": "class:a"},
        {"mechanism_family_id": "family:z"},
    ]
    diff = diff_mechanism_sets(baseline, candidate)
    cohort = cohort_summary({"baseline": baseline, "candidate": candidate})
    bundle = build_analysis_report_bundle(
        report_id=f"analysis-{runs[0]['run_id'][:8]}",
        lane_id="claims-triage.v1",
        decision_receipt=second["decision_receipt"],
        differential_result={"diff": diff, "cohort": cohort},
    )
    return {"status": "ok", "bundle": bundle, "source_runs": [runs[0]["run_id"], runs[1]["run_id"]]}


@app.post("/demo/submit")
def submit_demo(
    request: DemoSubmitRequest,
    auth_result: str = Depends(require_auth_token),
) -> dict[str, Any]:
    if request.requested_action not in ALLOWED_POLICY_ACTIONS:
        raise HTTPException(status_code=400, detail=f"unsupported requested action: {request.requested_action}")

    manifest_path, scorecard_path = _lane_asset_paths(request.lane_id)
    manifest = load_manifest(manifest_path)
    scorecard = _load_scorecard(scorecard_path)

    runner = _runner_for_profile(request.model_profile_id)
    if not profile_frozen(runner.profile):
        raise HTTPException(status_code=400, detail="model profile is not frozen")

    directories = _phase4_dirs(request.workspace)
    sequence = _next_sequence(directories["demo_runs"], "")
    seed = stable_hash(
        {
            "lane_id": request.lane_id,
            "profile": request.model_profile_id,
            "manifest_hash": manifest["payload"]["dataset_hash"],
            "scorecard": scorecard["artifact_id"],
            "sequence": sequence,
            "force_fallback": request.force_fallback,
        }
    )
    run_id = f"{request.lane_id}.{sequence:03d}.{seed[:8]}"
    trace_id = f"trace-{seed[:20]}"

    profile_record = runner.emit_model_profile_record(trace_id=trace_id, run_id=run_id)
    validate_instance(profile_record, REPO_ROOT / "schemas" / "model_profile_record.schema.json")

    run_config = build_run_config_record(
        lane_id=request.lane_id,
        model_profile_ref=profile_record["artifact_id"],
        dataset_manifest_ref=manifest["artifact_id"],
        scorecard_ref=scorecard["artifact_id"],
        runtime_flags={
            "requested_action": request.requested_action,
            "force_fallback": request.force_fallback,
        },
        fallback_config={
            "policy_fallback": True,
            "model_fallback": True,
            "operator_fallback": True,
        },
        replay_mode="immutable-manifest+run-config",
        seed_policy=runner.profile.seed_policy,
        trace_id=trace_id,
        run_id=run_id,
    )

    run_manifest = manifest
    if request.force_fallback:
        copied = read_json(manifest_path)
        copied["payload"]["items"][0]["input"]["force_fallback"] = True
        run_manifest = copied

    run_result = run_demo_lane(
        lane_id=request.lane_id,
        model_runner=runner,
        dataset_manifest=run_manifest,
        run_config=run_config,
        scorecard=scorecard,
        trace_id=trace_id,
        run_id=run_id,
        caller_id=auth_result,
    )

    replay_result = run_demo_lane(
        lane_id=request.lane_id,
        model_runner=runner,
        dataset_manifest=run_manifest,
        run_config=run_config,
        scorecard=scorecard,
        trace_id=trace_id,
        run_id=run_id,
        caller_id=auth_result,
    )
    replay_is_deterministic = deterministic_replay(run_result["outputs"], replay_result["outputs"])
    bundle_ref = store_bundle(run_result["bundle"], workspace=request.workspace)
    queue_status = queue_event(
        {
            "event": "demo_bundle_persisted",
            "run_id": run_id,
            "lane_id": request.lane_id,
            "bundle_hash": run_result["bundle"]["bundle_hash"],
            "backend": bundle_ref["backend"],
        }
    )

    demo_record = {
        "lane_id": request.lane_id,
        "run_id": run_id,
        "trace_id": trace_id,
        "model_profile_record": profile_record,
        "run_config_record": run_config,
        "dataset_manifest_hash": manifest["payload"]["dataset_hash"],
        "scorecard": scorecard,
        "deterministic_replay": replay_is_deterministic,
        "scoring": run_result["scoring"],
        "demo_run_record": run_result["demo_run_record"],
        "bundle": run_result["bundle"],
        "bundle_ref": bundle_ref,
        "queue_status": queue_status,
        "receipts": run_result["receipts"],
        "outputs": run_result["outputs"],
        "run_hash": run_result["run_hash"],
        "created_at": _utc_stamp(),
    }

    write_json(directories["demo_runs"] / f"{run_id}.json", demo_record)
    write_json(
        directories["demo_reports"] / f"{run_id}.json",
        {
            "run_id": run_id,
            "trace_id": trace_id,
            "report_bundle": run_result["bundle"],
            "report_bundle_ref": bundle_ref,
            "scoring": run_result["scoring"],
            "run_hash": run_result["run_hash"],
            "store_backend": store_backend(),
            "queue_backend": queue_backend(),
        },
    )
    for receipt in run_result["receipts"]:
        write_json(directories["demo_receipts"] / f"{receipt['receipt_id']}.json", receipt)

    return {
        "status": "ok",
        "run_id": run_id,
        "trace_id": trace_id,
        "lane_id": request.lane_id,
        "model_profile_id": request.model_profile_id,
        "deterministic_replay": replay_is_deterministic,
        "receipt_ids": [receipt["receipt_id"] for receipt in run_result["receipts"]],
        "fallback_stats": run_result["scoring"]["fallback_counters"],
        "performance": run_result["scoring"]["performance"],
        "success_rate": run_result["scoring"]["success_rate"],
        "fallback_rate": run_result["scoring"]["fallback_rate"],
        "report_bundle_hash": run_result["bundle"]["bundle_hash"],
        "report_bundle_ref": bundle_ref,
        "queue_status": queue_status,
    }


@app.get("/demo/receipt/{run_id}")
def get_demo_receipts(
    run_id: str,
    workspace: str = Query(..., min_length=1),
    _auth: str = Depends(require_auth_token),
) -> dict[str, Any]:
    run = _load_demo_run(workspace, run_id)
    return {
        "status": "ok",
        "run_id": run_id,
        "receipt_count": len(run.get("receipts", [])),
        "receipts": run.get("receipts", []),
    }


@app.get("/demo/report/{run_id}")
def get_demo_report(
    run_id: str,
    workspace: str = Query(..., min_length=1),
    _auth: str = Depends(require_auth_token),
) -> dict[str, Any]:
    directories = _phase4_dirs(workspace)
    report_path = directories["demo_reports"] / f"{run_id}.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail=f"demo report not found: {run_id}")
    return read_json(report_path)


@app.post("/pilot/submit")
def submit_pilot(
    request: PilotSubmitRequest,
    _auth: str = Depends(require_auth_token),
) -> dict[str, Any]:
    if request.requested_action not in ALLOWED_POLICY_ACTIONS:
        raise HTTPException(status_code=400, detail=f"unsupported requested action: {request.requested_action}")

    scope_record = _load_or_create_scope_record(request.workspace)
    decision = scope_decision(
        scope_record,
        user_id=request.user_id,
        task=request.task,
        corpus=request.corpus,
        action=request.requested_action,
    )
    if not decision["allowed"]:
        raise HTTPException(status_code=403, detail=f"pilot scope rejected: {decision['reason']}")

    demo_run_id = request.demo_run_id or _latest_demo_run_for_lane(request.workspace, request.lane_id)
    if not demo_run_id:
        raise HTTPException(status_code=404, detail="no demo run available for requested lane")

    demo_run = _load_demo_run(request.workspace, demo_run_id)
    routing_action = demo_run.get("outputs", [{}])[0].get("lane_action", request.requested_action)

    directories = _phase4_dirs(request.workspace)
    sequence = _next_sequence(directories["pilot_runs"], "")
    pilot_run_id = f"pilot.{request.lane_id}.{sequence:03d}"
    trace_id = f"pilot-trace-{stable_hash({'pilot_run_id': pilot_run_id, 'demo_run_id': demo_run_id})[:16]}"

    pilot_record = build_pilot_run_record(
        pilot_scope_ref=scope_record["artifact_id"],
        lane_id=request.lane_id,
        demo_run_ref=demo_run_id,
        review_status="pending",
        policy_routing_outcome=routing_action,
        adjudication_outcome="pending",
        trace_id=trace_id,
        run_id=pilot_run_id,
    )
    write_json(directories["pilot_runs"] / f"{pilot_run_id}.json", pilot_record)

    return {
        "status": "ok",
        "pilot_run_id": pilot_run_id,
        "scope_policy_id": scope_record["artifact_id"],
        "review_required": decision["review_required"],
        "policy_routing_outcome": routing_action,
        "demo_run_id": demo_run_id,
    }


@app.post("/pilot/review")
def submit_pilot_review(
    request: PilotReviewRequest,
    _auth: str = Depends(require_auth_token),
) -> dict[str, Any]:
    directories = _phase4_dirs(request.workspace)
    pilot_run_path = directories["pilot_runs"] / f"{request.pilot_run_id}.json"
    if not pilot_run_path.exists():
        raise HTTPException(status_code=404, detail=f"pilot run not found: {request.pilot_run_id}")

    scope_record = _load_or_create_scope_record(request.workspace)
    review_record = build_operator_review_record(
        raw_reviewer_id=request.reviewer_id,
        identity_key_id=scope_record["payload"]["identity_key_id"],
        salt=scope_record["payload"]["policy_version"],
        task_ref=request.task_ref,
        accepted=request.accepted,
        override=request.override,
        explanation_usefulness=request.explanation_usefulness,
        receipt_usefulness=request.receipt_usefulness,
        escalation_appropriateness=request.escalation_appropriateness,
        confidence_calibration_agreement=request.confidence_calibration_agreement,
        trace_id=f"review-trace-{request.pilot_run_id}",
        run_id=f"review-{request.pilot_run_id}",
    )

    review_path = directories["pilot_reviews"] / f"{request.pilot_run_id}.{review_record['payload']['review_record_id']}.json"
    write_json(review_path, review_record)

    return {
        "status": "ok",
        "pilot_run_id": request.pilot_run_id,
        "review_record_id": review_record["payload"]["review_record_id"],
        "reviewer_pseudonym": review_record["payload"]["reviewer_pseudonym"],
    }


@app.get("/pilot/receipt/{run_id}")
def get_pilot_receipts(
    run_id: str,
    workspace: str = Query(..., min_length=1),
    _auth: str = Depends(require_auth_token),
) -> dict[str, Any]:
    directories = _phase4_dirs(workspace)
    pilot_run_path = directories["pilot_runs"] / f"{run_id}.json"
    if not pilot_run_path.exists():
        raise HTTPException(status_code=404, detail=f"pilot run not found: {run_id}")

    pilot_run = read_json(pilot_run_path)
    demo_run = _load_demo_run(workspace, pilot_run["payload"]["demo_run_ref"])
    return {
        "status": "ok",
        "pilot_run_id": run_id,
        "demo_run_id": pilot_run["payload"]["demo_run_ref"],
        "receipts": demo_run.get("receipts", []),
    }


@app.get("/pilot/metrics")
def get_pilot_metrics(
    workspace: str = Query(..., min_length=1),
    _auth: str = Depends(require_auth_token),
) -> dict[str, Any]:
    directories = _phase4_dirs(workspace)
    scope_record = _load_or_create_scope_record(workspace)

    pilot_run_records = [read_json(path) for path in sorted(directories["pilot_runs"].glob("*.json"))]
    review_records = [read_json(path) for path in sorted(directories["pilot_reviews"].glob("*.json"))]

    trust = compute_trust_metrics(review_records)
    total = max(1, len(pilot_run_records))
    false_allow_count = sum(
        1
        for record in pilot_run_records
        if record["payload"]["policy_routing_outcome"] == "allow"
        and record["payload"].get("adjudication_outcome") == "incorrect"
    )
    false_block_count = sum(
        1
        for record in pilot_run_records
        if record["payload"]["policy_routing_outcome"] == "block"
        and record["payload"].get("adjudication_outcome") == "incorrect"
    )
    false_allow_rate = false_allow_count / total
    false_block_rate = false_block_count / total
    routing_quality = max(0.0, 1.0 - (false_allow_rate + false_block_rate))

    baseline = {"family-a": max(1, len(pilot_run_records))}
    current = {"family-a": len(pilot_run_records)}
    drift_metric = compute_drift_metric(baseline, current)
    drift_alert = build_drift_alert_record(
        cohort_ref="pilot-window",
        mechanism_family_id="family-a",
        drift_metric=drift_metric,
        threshold=0.4,
        supporting_refs=[record["artifact_id"] for record in pilot_run_records],
        trace_id="pilot-metrics-trace",
        run_id="pilot-metrics-run",
    )
    write_json(directories["pilot_metrics"] / "drift_alert_record.json", drift_alert)

    metrics_bundle = build_pilot_metrics_bundle(
        pilot_scope_ref=scope_record["artifact_id"],
        window_id="pilot-window",
        false_allow_rate=false_allow_rate,
        false_block_rate=false_block_rate,
        routing_quality=routing_quality,
        trust_metrics=trust,
        drift_summary={
            "drift_metric": drift_metric,
            "alert_status": drift_alert["payload"]["alert_status"],
        },
        trace_id="pilot-metrics-trace",
        run_id="pilot-metrics-run",
    )
    write_json(directories["pilot_metrics"] / "pilot_metrics_bundle.json", metrics_bundle)

    return {
        "status": "ok",
        "pilot_scope_policy_record": scope_record,
        "pilot_run_count": len(pilot_run_records),
        "review_count": len(review_records),
        "metrics_bundle": metrics_bundle,
        "drift_alert_record": drift_alert,
    }
