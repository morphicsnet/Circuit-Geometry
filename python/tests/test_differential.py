from geoclt.differential import cohort_summary, diff_mechanism_sets


def test_diff_deterministic_on_same_input():
    baseline = [{"mechanism_id": "m1", "mechanism_class_id": "c1"}]
    candidate = [
        {"mechanism_id": "m1", "mechanism_class_id": "c1"},
        {"mechanism_family_id": "f2"},
    ]
    one = diff_mechanism_sets(baseline, candidate)
    two = diff_mechanism_sets(baseline, candidate)
    assert one == two


def test_diff_ignores_raw_feature_noise():
    clean = diff_mechanism_sets(
        [{"mechanism_id": "m1"}],
        [{"mechanism_id": "m1"}, {"mechanism_family_id": "f2"}],
    )
    noisy = diff_mechanism_sets(
        [{"mechanism_id": "m1", "raw_feature": "x"}],
        [{"mechanism_id": "m1", "raw_feature": "y"}, {"mechanism_family_id": "f2"}],
    )
    assert clean["diff_hash"] == noisy["diff_hash"]


def test_cohort_summary_deterministic():
    cohorts = {
        "b": [{"mechanism_id": "m1"}],
        "a": [{"mechanism_id": "m1"}, {"mechanism_family_id": "f1"}],
    }
    one = cohort_summary(cohorts)
    two = cohort_summary(cohorts)
    assert one == two
