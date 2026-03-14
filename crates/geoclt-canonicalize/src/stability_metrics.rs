pub fn stability_score(values: &[String]) -> f64 {
    if values.is_empty() {
        return 0.0;
    }
    let first = &values[0];
    let stable_count = values.iter().filter(|value| *value == first).count();
    stable_count as f64 / values.len() as f64
}

pub fn is_stable(values: &[String], threshold: f64) -> bool {
    stability_score(values) >= threshold
}

#[cfg(test)]
mod tests {
    use super::{is_stable, stability_score};

    #[test]
    fn computes_stability_ratio() {
        let score = stability_score(&["a".to_string(), "a".to_string(), "b".to_string()]);
        assert!((score - 0.666666).abs() < 0.001);
        assert!(is_stable(&["a".to_string(), "a".to_string()], 1.0));
    }
}
