from __future__ import annotations

from typing import Any

from .._paths import schema_path
from ..artifacts import build_artifact_entry, validate_instance


def build_pilot_scope_policy_record(
    *,
    policy_id: str,
    policy_version: str,
    identity_key_id: str,
    in_scope_users: list[str],
    in_scope_tasks: list[str],
    allowed_corpora: list[str],
    review_required_actions: list[str],
    prohibited_actions: list[str],
    trace_id: str,
    run_id: str,
) -> dict[str, Any]:
    record = build_artifact_entry(
        artifact_type="pilot_scope_policy_record",
        schema_version=1,
        producer="geoclt:pilot:0.4.0",
        trace_id=trace_id,
        run_id=run_id,
        payload={
            "policy_id": policy_id,
            "policy_version": policy_version,
            "identity_key_id": identity_key_id,
            "in_scope_users": sorted(in_scope_users),
            "in_scope_tasks": sorted(in_scope_tasks),
            "allowed_corpora": sorted(allowed_corpora),
            "review_required_actions": sorted(review_required_actions),
            "prohibited_actions": sorted(prohibited_actions),
        },
        created_at="2026-01-01T00:00:00Z",
    )
    validate_instance(record, schema_path("pilot_scope_policy_record.schema.json"))
    return record


def in_scope(scope_record: dict[str, Any], *, user_id: str, task: str, corpus: str, action: str) -> bool:
    decision = scope_decision(
        scope_record,
        user_id=user_id,
        task=task,
        corpus=corpus,
        action=action,
    )
    return decision["allowed"]


def scope_decision(
    scope_record: dict[str, Any], *, user_id: str, task: str, corpus: str, action: str
) -> dict[str, Any]:
    payload = scope_record["payload"]
    if user_id not in payload["in_scope_users"]:
        return {"allowed": False, "reason": "user_out_of_scope", "review_required": False}
    if task not in payload["in_scope_tasks"]:
        return {"allowed": False, "reason": "task_out_of_scope", "review_required": False}
    if corpus not in payload["allowed_corpora"]:
        return {"allowed": False, "reason": "corpus_out_of_scope", "review_required": False}
    if action in payload["prohibited_actions"]:
        return {"allowed": False, "reason": "action_prohibited", "review_required": False}
    return {
        "allowed": True,
        "reason": "ok",
        "review_required": action in payload["review_required_actions"],
    }
