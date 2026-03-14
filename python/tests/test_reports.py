from geoclt.reports import build_analysis_report_bundle, report_bundle_identity_stable


def test_report_bundle_hash_stable_for_same_payload():
    receipt = {"receipt_id": "r1", "decision": "allow"}
    differential = {"diff_hash": "abc"}
    one = build_analysis_report_bundle(
        report_id="report-1",
        lane_id="claims-triage.v1",
        decision_receipt=receipt,
        differential_result=differential,
    )
    two = build_analysis_report_bundle(
        report_id="report-1",
        lane_id="claims-triage.v1",
        decision_receipt=receipt,
        differential_result=differential,
    )
    assert one["bundle_hash"] == two["bundle_hash"]
    assert report_bundle_identity_stable(one)
