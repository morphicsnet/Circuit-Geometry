use pyo3::prelude::*;

fn stages() -> Vec<&'static str> {
    vec![
        "atlas",
        "metric",
        "transport",
        "hypergraph",
        "verify_mechanisms",
        "canonicalize",
        "benchmark",
    ]
}

#[pyfunction]
fn benchmark_stage_names() -> Vec<String> {
    stages().into_iter().map(str::to_string).collect()
}

pub fn bind(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("BENCHMARK_STAGES", benchmark_stage_names())?;
    m.add_function(wrap_pyfunction!(benchmark_stage_names, m)?)?;
    Ok(())
}
