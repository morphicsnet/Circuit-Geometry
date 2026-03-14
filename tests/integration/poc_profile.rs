#[test]
fn poc_profile_smoke_test() {
    let lane_id = "factual_retrieval.v1";
    let behavior_id = "factual_retrieval";
    assert!(lane_id.ends_with(".v1"));
    assert_eq!(behavior_id, "factual_retrieval");
}
