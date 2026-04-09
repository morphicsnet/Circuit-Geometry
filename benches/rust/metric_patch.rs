use geoclt_atlas::atlas::fit_atlas;
use geoclt_metric::metric::estimate_pullback_metric;

fn main() {
    let feature_hints = vec!["sae:f12".to_string(), "head:5:3".to_string()];
    let atlas = fit_atlas("gpt2", "factual_retrieval.v1", "factual_retrieval", &feature_hints)
        .expect("atlas");
    let metric = estimate_pullback_metric("factual_retrieval.v1", &atlas, &feature_hints)
        .expect("metric");
    println!("{}", serde_json::to_string_pretty(&metric).expect("metric json"));
}
