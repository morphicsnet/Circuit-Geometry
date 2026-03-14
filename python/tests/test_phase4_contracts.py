from __future__ import annotations

from pathlib import Path

from geoclt.artifacts import read_json, stable_hash, validate_instance
from geoclt.demo import build_manifest, build_run_config_record, build_scorecard
from geoclt.field_trials import (
    build_operator_review_record,
    build_pilot_metrics_bundle,
    build_pilot_run_record,
    build_pilot_scope_policy_record,
    in_scope,
    pseudonymous_reviewer_id,
)
from geoclt.models import DEFAULT_PHI_PROFILE, DEFAULT_QWEN_PROFILE, profile_frozen


def _schema_path(name: str) -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / name


def test_phase4_schema_registry_has_new_artifacts():
    registry = read_json(Path(__file__).resolve().parents[2] / "schemas" / "registry.json")
    expected = {
        "model_profile_record",
        "golden_dataset_manifest",
        "run_config_record",
        "demo_run_record",
        "demo_scorecard",
        "pilot_scope_policy_record",
        "pilot_run_record",
        "operator_review_record",
        "drift_alert_record",
        "pilot_metrics_bundle",
    }
    assert expected.issubset(set(registry["artifacts"].keys()))


def test_phase4_artifact_builders_validate_against_schema():
    manifest = build_manifest(
        dataset_id="d1",
        dataset_version="v1",
        lane_id="realworld-claims-triage.v1",
        items=[
            {
                "item_id": "i1",
                "input": {"text": "hello"},
                "expected_output": {"label": "allow"},
                "label": "positive",
            }
        ],
        provenance={"source": "test"},
        expected_schema={"type": "object"},
        labels=["positive"],
        ambiguity_flags=[],
        trace_id="t1",
        run_id="r1",
    )
    validate_instance(manifest, _schema_path("golden_dataset_manifest.schema.json"))

    scorecard = build_scorecard(
        lane_id="realworld-claims-triage.v1",
        success_condition="ok",
        acceptable_fallback_condition="review",
        failure_condition="bad",
        latency_budget_ms=1000,
        escalation_rules=["review"],
        thresholds={"success_rate_min": 0.8, "success_confidence_min": 0.5, "evidence_alignment_min": 0.5},
        trace_id="t1",
        run_id="r1",
    )
    validate_instance(scorecard, _schema_path("demo_scorecard.schema.json"))

    run_config = build_run_config_record(
        lane_id="realworld-claims-triage.v1",
        model_profile_ref="artifact-profile",
        dataset_manifest_ref=manifest["artifact_id"],
        scorecard_ref=scorecard["artifact_id"],
        runtime_flags={"flag": True},
        fallback_config={"policy_fallback": True},
        replay_mode="immutable",
        seed_policy="fixed:42",
        trace_id="t1",
        run_id="r1",
    )
    validate_instance(run_config, _schema_path("run_config_record.schema.json"))


def test_phase4_profile_freeze_and_hash_stability():
    assert profile_frozen(DEFAULT_QWEN_PROFILE)
    assert profile_frozen(DEFAULT_PHI_PROFILE)
    assert stable_hash(DEFAULT_QWEN_PROFILE.as_record_payload()) == stable_hash(
        DEFAULT_QWEN_PROFILE.as_record_payload()
    )


def test_phase4_pilot_artifact_contracts():
    scope = build_pilot_scope_policy_record(
        policy_id="policy",
        policy_version="v1",
        identity_key_id="k1",
        in_scope_users=["u1"],
        in_scope_tasks=["claims-triage"],
        allowed_corpora=["golden"],
        review_required_actions=["allow_with_review"],
        prohibited_actions=["autonomous_execute"],
        trace_id="t",
        run_id="r",
    )
    validate_instance(scope, _schema_path("pilot_scope_policy_record.schema.json"))
    assert in_scope(scope, user_id="u1", task="claims-triage", corpus="golden", action="allow")
    assert not in_scope(scope, user_id="u2", task="claims-triage", corpus="golden", action="allow")

    pilot_run = build_pilot_run_record(
        pilot_scope_ref=scope["artifact_id"],
        lane_id="realworld-claims-triage.v1",
        demo_run_ref="demo-1",
        review_status="pending",
        policy_routing_outcome="allow",
        adjudication_outcome="pending",
        trace_id="t",
        run_id="pilot-1",
    )
    validate_instance(pilot_run, _schema_path("pilot_run_record.schema.json"))

    review = build_operator_review_record(
        raw_reviewer_id="alice@example.com",
        identity_key_id="k1",
        salt="v1",
        task_ref="task-1",
        accepted=True,
        override=False,
        explanation_usefulness=0.9,
        receipt_usefulness=0.9,
        escalation_appropriateness=0.9,
        confidence_calibration_agreement=0.9,
        trace_id="t",
        run_id="r",
    )
    validate_instance(review, _schema_path("operator_review_record.schema.json"))
    assert "alice@example.com" not in review["payload"]["reviewer_pseudonym"]

    bundle = build_pilot_metrics_bundle(
        pilot_scope_ref=scope["artifact_id"],
        window_id="w1",
        false_allow_rate=0.0,
        false_block_rate=0.0,
        routing_quality=1.0,
        trust_metrics={
            "reviewer_acceptance_rate": 1.0,
            "reviewer_override_rate": 0.0,
            "explanation_usefulness_score": 0.9,
            "receipt_usefulness_score": 0.9,
            "escalation_appropriateness_rate": 0.9,
            "confidence_calibration_agreement": 0.9,
        },
        drift_summary={"drift_metric": 0.0, "alert_status": "ok"},
        trace_id="t",
        run_id="r",
    )
    validate_instance(bundle, _schema_path("pilot_metrics_bundle.schema.json"))


def test_phase4_reviewer_pseudonym_stable_within_policy_version():
    one = pseudonymous_reviewer_id("reviewer-raw", "key-v1", "policy-v1")
    two = pseudonymous_reviewer_id("reviewer-raw", "key-v1", "policy-v1")
    rotated = pseudonymous_reviewer_id("reviewer-raw", "key-v2", "policy-v2")
    assert one == two
    assert one != rotated
