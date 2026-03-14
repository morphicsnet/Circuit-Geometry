#[derive(Debug, Clone)]
pub struct VerificationResult {
    pub causal_delta: f64,
    pub synergy: f64,
    pub passed: bool,
}

pub fn verify(causal_delta: f64, synergy: f64, delta_threshold: f64, synergy_threshold: f64) -> VerificationResult {
    VerificationResult {
        causal_delta,
        synergy,
        passed: causal_delta >= delta_threshold && synergy >= synergy_threshold,
    }
}
