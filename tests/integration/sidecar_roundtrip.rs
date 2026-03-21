use geoclt_artifacts::registry::load_registry_from_path;
use geoclt_sidecar::server::SidecarServer;

#[test]
fn sidecar_roundtrip_phase2() {
    let registry_path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../schemas/registry.json");
    let registry = load_registry_from_path(&registry_path).expect("registry");
    let mut sidecar = SidecarServer::new("geoclt:sidecar:0.2.0", registry);

    sidecar
        .start_trace(
            "trace-integration-1",
            "transformers",
            "gpt2-small",
            "factual_retrieval.v1",
            "run-integration-1",
            "2026-01-01T00:00:00Z",
        )
        .expect("start trace");

    sidecar
        .push_chunk("trace-integration-1", "chunk-1", b"abc".to_vec())
        .expect("push chunk");

    let bundle = sidecar
        .end_trace("trace-integration-1")
        .expect("end trace");
    assert!(bundle.immutable);
    assert_eq!(bundle.trace_id, "trace-integration-1");
    assert_eq!(sidecar.active_traces(), 0);
}

#[test]
fn sidecar_abort_cleans_active_trace() {
    let registry_path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../schemas/registry.json");
    let registry = load_registry_from_path(&registry_path).expect("registry");
    let mut sidecar = SidecarServer::new("geoclt:sidecar:0.2.0", registry);

    sidecar
        .start_trace(
            "trace-abort-1",
            "transformers",
            "gpt2-small",
            "factual_retrieval.v1",
            "run-abort-1",
            "2026-01-01T00:00:00Z",
        )
        .expect("start trace");
    assert_eq!(sidecar.active_traces(), 1);

    sidecar.abort_trace("trace-abort-1").expect("abort trace");
    assert_eq!(sidecar.active_traces(), 0);
}
