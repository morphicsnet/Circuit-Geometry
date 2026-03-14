from __future__ import annotations

from typing import Any

from ..artifacts import stable_hash


def replay_hash(outputs: list[dict[str, Any]]) -> str:
    canonical = [
        {
            "item_id": item["item_id"],
            "result": item["result"],
            "routing_label": item["result"].get("routing_label"),
        }
        for item in sorted(outputs, key=lambda row: row["item_id"])
    ]
    return stable_hash(canonical)


def deterministic_replay(first_outputs: list[dict[str, Any]], second_outputs: list[dict[str, Any]]) -> bool:
    return replay_hash(first_outputs) == replay_hash(second_outputs)
