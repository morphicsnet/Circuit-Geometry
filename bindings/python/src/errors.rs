use pyo3::prelude::*;

#[allow(dead_code)]
pub fn native_error(error: impl ToString) -> PyErr {
    pyo3::exceptions::PyRuntimeError::new_err(error.to_string())
}
