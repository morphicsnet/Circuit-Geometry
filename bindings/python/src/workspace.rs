use pyo3::prelude::*;

fn stages() -> Vec<&'static str> {
    vec![
        "fit_atlas",
        "fit_transport",
        "propose_events",
        "verify_mechanisms",
        "run_workspace_bundle",
        "run_benchmark",
    ]
}

#[pyfunction]
fn workspace_stage_names() -> Vec<String> {
    stages().into_iter().map(str::to_string).collect()
}

#[pyfunction]
fn workspace_contract() -> String {
    serde_json::json!({
        "stages": stages(),
        "kernel_entrypoints": [
            "run_workspace_kernels_json",
            "run_workspace_bundle_json",
        ],
        "artifact_families": [
            "atlas_overlap_map",
            "transport_diagnostics",
            "candidate_event_table",
            "admitted_hyperpath_table",
            "falsifier_sheet"
            ,
            "artifact_bundle"
        ],
    })
    .to_string()
}

pub fn bind(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("WORKSPACE_STAGES", workspace_stage_names())?;
    m.add_function(wrap_pyfunction!(workspace_stage_names, m)?)?;
    m.add_function(wrap_pyfunction!(workspace_contract, m)?)?;
    Ok(())
}
