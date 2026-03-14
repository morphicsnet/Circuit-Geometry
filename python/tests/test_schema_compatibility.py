from geoclt.artifacts import build_artifact_bundle, build_artifact_entry, verify_bundle_manifest


def _sample_artifact(version: int) -> dict:
    return build_artifact_entry(
        artifact_type="event_record",
        schema_version=version,
        producer="geoclt:mock-adapter:0.2.0",
        trace_id="trace-1",
        run_id="run-1",
        payload={"x": 1},
        created_at="2026-01-01T00:00:00Z",
    )


def test_bundle_manifest_verification():
    bundle = build_artifact_bundle(
        run_id="run-1",
        trace_id="trace-1",
        producer="geoclt:sidecar:0.2.0",
        artifacts=[_sample_artifact(2)],
        transitional=False,
        immutable=True,
        created_at="2026-01-01T00:00:00Z",
    )
    assert verify_bundle_manifest(bundle) is True


def test_n_and_n_minus_1_supported_shape():
    current = _sample_artifact(2)
    previous = _sample_artifact(1)
    assert current["schema_version"] == 2
    assert previous["schema_version"] == 1
