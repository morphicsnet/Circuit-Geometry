use sha2::{Digest, Sha256};

pub fn derive_cluster_id(member_mechanism_ids: &[String]) -> String {
    let mut members = member_mechanism_ids.to_vec();
    members.sort();
    members.dedup();
    let payload = serde_json::json!({"member_mechanism_ids": members});
    let bytes = serde_jcs::to_vec(&payload).expect("canonical cluster payload");
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("cluster-{:x}", hasher.finalize())
}

pub fn cluster_is_deterministic(member_mechanism_ids: &[String]) -> bool {
    derive_cluster_id(member_mechanism_ids) == derive_cluster_id(member_mechanism_ids)
}

#[cfg(test)]
mod tests {
    use super::derive_cluster_id;

    #[test]
    fn cluster_id_is_order_invariant() {
        let one = derive_cluster_id(&["m2".to_string(), "m1".to_string()]);
        let two = derive_cluster_id(&["m1".to_string(), "m2".to_string()]);
        assert_eq!(one, two);
    }
}
