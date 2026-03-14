from dataclasses import dataclass


@dataclass(slots=True)
class BenchmarkLaneConfig:
    lane_id: str
    behavior_id: str
    intervention_delta_threshold: float = 0.10
    synergy_threshold: float = 0.05
    chart_stability_threshold: float = 0.70
    transport_coherence_threshold: float = 0.70
    baseline_margin_threshold: float = 0.05
