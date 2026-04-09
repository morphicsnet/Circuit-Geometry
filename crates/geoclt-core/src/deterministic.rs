use serde::Serialize;
use sha2::{Digest, Sha256};

use crate::{GeoCltError, GeoCltResult};

fn canonical_bytes<T: Serialize>(value: &T) -> GeoCltResult<Vec<u8>> {
    serde_jcs::to_vec(value).map_err(|error| {
        GeoCltError::Serialization(format!("failed to canonicalize payload: {error}"))
    })
}

pub fn stable_hash<T: Serialize>(value: &T) -> GeoCltResult<String> {
    let bytes = canonical_bytes(value)?;
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    Ok(format!("{:x}", hasher.finalize()))
}

pub fn stable_ratio<T: Serialize>(value: &T, label: &str) -> GeoCltResult<f64> {
    let digest = stable_hash(&serde_json::json!({ "label": label, "value": value }))?;
    let window = u64::from_str_radix(&digest[..16], 16).map_err(|error| {
        GeoCltError::Internal(format!("failed to decode digest window: {error}"))
    })?;
    Ok(window as f64 / u64::MAX as f64)
}

pub fn bounded_f64<T: Serialize>(
    value: &T,
    label: &str,
    lower: f64,
    upper: f64,
) -> GeoCltResult<f64> {
    if !lower.is_finite() || !upper.is_finite() || lower > upper {
        return Err(GeoCltError::Validation(format!(
            "invalid bounds for {label}: lower={lower}, upper={upper}"
        )));
    }
    let ratio = stable_ratio(value, label)?;
    Ok(lower + (upper - lower) * ratio)
}

pub fn bounded_u32<T: Serialize>(
    value: &T,
    label: &str,
    lower: u32,
    upper: u32,
) -> GeoCltResult<u32> {
    if lower > upper {
        return Err(GeoCltError::Validation(format!(
            "invalid bounds for {label}: lower={lower}, upper={upper}"
        )));
    }
    if lower == upper {
        return Ok(lower);
    }
    let ratio = stable_ratio(value, label)?;
    let span = (upper - lower) as f64;
    Ok(lower + (ratio * span).round() as u32)
}

pub fn clamp(value: f64, lower: f64, upper: f64) -> f64 {
    value.max(lower).min(upper)
}

#[cfg(test)]
mod tests {
    use super::{bounded_f64, bounded_u32, stable_hash};

    #[test]
    fn stable_hash_is_deterministic() {
        let one = stable_hash(&serde_json::json!({"a": 1, "b": 2})).expect("hash one");
        let two = stable_hash(&serde_json::json!({"b": 2, "a": 1})).expect("hash two");
        assert_eq!(one, two);
    }

    #[test]
    fn bounded_helpers_stay_in_range() {
        let payload = serde_json::json!({"stage": "atlas"});
        let score = bounded_f64(&payload, "score", 0.1, 0.9).expect("score");
        let count = bounded_u32(&payload, "count", 3, 7).expect("count");
        assert!((0.1..=0.9).contains(&score));
        assert!((3..=7).contains(&count));
    }
}
