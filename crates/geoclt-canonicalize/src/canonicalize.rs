pub fn canonical_mechanism_key(parts: &[&str]) -> String {
    parts.join("::")
}
