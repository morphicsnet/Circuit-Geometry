use pyo3::prelude::*;

#[pyfunction]
fn native_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

#[pyfunction]
fn canonical_hash(payload: &str) -> PyResult<String> {
    let value: serde_json::Value = serde_json::from_str(payload)
        .map_err(|error| pyo3::exceptions::PyValueError::new_err(error.to_string()))?;
    geoclt_artifacts::canonicalize::content_hash(&value)
        .map_err(pyo3::exceptions::PyValueError::new_err)
}

#[pyfunction]
fn validate_json(instance: &str, schema: &str) -> PyResult<bool> {
    geoclt_artifacts::validate::validate_json_against_schema(instance, schema)
        .map(|_| true)
        .map_err(pyo3::exceptions::PyValueError::new_err)
}

#[pyfunction]
fn run_benchmark_hook(run_id: &str, trace_id: &str) -> PyResult<String> {
    let (_graph, bundle) = geoclt_runtime::run::execute_batch_graph(run_id, trace_id)
        .map_err(pyo3::exceptions::PyRuntimeError::new_err)?;
    Ok(bundle.bundle_hash)
}

#[pymodule]
fn geoclt_native(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(native_version, m)?)?;
    m.add_function(wrap_pyfunction!(canonical_hash, m)?)?;
    m.add_function(wrap_pyfunction!(validate_json, m)?)?;
    m.add_function(wrap_pyfunction!(run_benchmark_hook, m)?)?;
    Ok(())
}
