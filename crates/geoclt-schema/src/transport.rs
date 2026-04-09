use geoclt_units::Score;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TransportDiagnostics {
    pub lane_id: String,
    pub context_id: String,
    pub loop_consistency: Score,
    pub distortion: Score,
    pub coherence: Score,
    pub geodesic_deviation: Score,
    pub transport_edge_ids: Vec<String>,
}
