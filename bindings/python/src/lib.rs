use pyo3::prelude::*;

mod artifacts;
mod benchmark;
mod errors;
mod sidecar;
mod workspace;

#[pymodule]
fn geoclt_native(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    geoclt_ffi::register_module(m)?;
    artifacts::bind(m)?;
    benchmark::bind(m)?;
    sidecar::bind(m)?;
    workspace::bind(m)?;
    Ok(())
}
