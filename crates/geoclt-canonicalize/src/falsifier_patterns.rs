pub fn falsifier_pattern_key(flags: &[(String, bool)]) -> String {
    let mut enabled = flags
        .iter()
        .filter(|(_, value)| *value)
        .map(|(key, _)| key.clone())
        .collect::<Vec<_>>();
    enabled.sort();
    if enabled.is_empty() {
        return "none".to_string();
    }
    enabled.join("+")
}

#[cfg(test)]
mod tests {
    use super::falsifier_pattern_key;

    #[test]
    fn creates_deterministic_pattern_keys() {
        let key = falsifier_pattern_key(&[
            ("chart_fragility".to_string(), false),
            ("spurious_synergy".to_string(), true),
            ("pairwise_sufficiency".to_string(), true),
        ]);
        assert_eq!(key, "pairwise_sufficiency+spurious_synergy");
    }
}
