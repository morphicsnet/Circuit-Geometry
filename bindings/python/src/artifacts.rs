use pyo3::prelude::*;

fn families() -> Vec<&'static str> {
    vec![
        "atlas_overlap_map",
        "transport_diagnostics",
        "candidate_event_table",
        "admitted_hyperpath_table",
        "falsifier_sheet",
    ]
}

#[pyfunction]
fn artifact_families() -> Vec<String> {
    families().into_iter().map(str::to_string).collect()
}

pub fn bind(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("ARTIFACT_FAMILIES", artifact_families())?;
    m.add_function(wrap_pyfunction!(artifact_families, m)?)?;
    Ok(())
}
