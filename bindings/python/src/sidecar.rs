use pyo3::prelude::*;

fn capabilities() -> Vec<&'static str> {
    vec!["stream_trace", "emit_bundle", "status_probe"]
}

#[pyfunction]
fn sidecar_capabilities() -> Vec<String> {
    capabilities().into_iter().map(str::to_string).collect()
}

pub fn bind(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("SIDECAR_CAPABILITIES", sidecar_capabilities())?;
    m.add_function(wrap_pyfunction!(sidecar_capabilities, m)?)?;
    Ok(())
}
