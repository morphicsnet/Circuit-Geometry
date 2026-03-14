#[derive(Debug, Clone)]
pub struct TransportDiagnostics {
    pub loop_consistency: f64,
    pub distortion: f64,
    pub coherence: f64,
}
