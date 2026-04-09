//! Internal PyO3 bridge exposing Geo-CLT kernels and runtime bundles to Python.
#![allow(clippy::useless_conversion)]

use pyo3::prelude::*;
use serde::de::DeserializeOwned;
use serde::Deserialize;

use geoclt_atlas::atlas::fit_atlas;
use geoclt_causal::verify::verify_mechanisms;
use geoclt_hypergraph::induce::{materialize_hyperpaths, propose_events};
use geoclt_metric::metric::estimate_pullback_metric;
use geoclt_runtime::run::{
    execute_workspace_bundle, execute_workspace_kernels, WorkspaceKernelInput,
};
use geoclt_schema::atlas::AtlasOverlapMap;
use geoclt_schema::benchmark::BenchmarkLane;
use geoclt_schema::event::CandidateEventTable;
use geoclt_schema::hyperpath::AdmittedHyperpathTable;
use geoclt_schema::metric::MetricEstimate;
use geoclt_schema::transport::TransportDiagnostics;
use geoclt_transport::transport::fit_transport;

#[derive(Debug, Deserialize)]
struct AtlasRequest {
    model_id: String,
    lane_id: String,
    profile: String,
    #[serde(default)]
    feature_hints: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct MetricRequest {
    lane_id: String,
    atlas: AtlasOverlapMap,
    #[serde(default)]
    feature_hints: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct TransportRequest {
    lane_id: String,
    atlas: AtlasOverlapMap,
    metric: MetricEstimate,
}

#[derive(Debug, Deserialize)]
struct HypergraphRequest {
    lane_id: String,
    behavior_id: String,
    transport: TransportDiagnostics,
    #[serde(default)]
    feature_hints: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct HyperpathRequest {
    lane_id: String,
    behavior_id: String,
    candidate_event_table: CandidateEventTable,
    atlas: AtlasOverlapMap,
    transport: TransportDiagnostics,
    intervention_faithfulness: f64,
    synergy_score_max: f64,
    chart_stability: f64,
    geodesic_deviation: f64,
}

#[derive(Debug, Deserialize)]
struct CausalRequest {
    lane: BenchmarkLane,
    hyperpaths: AdmittedHyperpathTable,
}

fn py_value_error(error: impl ToString) -> PyErr {
    pyo3::exceptions::PyValueError::new_err(error.to_string())
}

fn parse_json<T: DeserializeOwned>(payload: &str) -> PyResult<T> {
    serde_json::from_str(payload).map_err(py_value_error)
}

fn to_json<T: serde::Serialize>(value: &T) -> PyResult<String> {
    serde_json::to_string(value).map_err(py_value_error)
}

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
fn fit_atlas_json(payload: &str) -> PyResult<String> {
    let request: AtlasRequest = parse_json(payload)?;
    let atlas = fit_atlas(
        &request.model_id,
        &request.lane_id,
        &request.profile,
        &request.feature_hints,
    )
    .map_err(py_value_error)?;
    to_json(&atlas)
}

#[pyfunction]
fn estimate_pullback_metric_json(payload: &str) -> PyResult<String> {
    let request: MetricRequest = parse_json(payload)?;
    let metric = estimate_pullback_metric(&request.lane_id, &request.atlas, &request.feature_hints)
        .map_err(py_value_error)?;
    to_json(&metric)
}

#[pyfunction]
fn fit_transport_json(payload: &str) -> PyResult<String> {
    let request: TransportRequest = parse_json(payload)?;
    let transport =
        fit_transport(&request.lane_id, &request.atlas, &request.metric).map_err(py_value_error)?;
    to_json(&transport)
}

#[pyfunction]
fn propose_events_json(payload: &str) -> PyResult<String> {
    let request: HypergraphRequest = parse_json(payload)?;
    let events = propose_events(
        &request.lane_id,
        &request.behavior_id,
        &request.transport,
        &request.feature_hints,
    )
    .map_err(py_value_error)?;
    to_json(&events)
}

#[pyfunction]
fn materialize_hyperpaths_json(payload: &str) -> PyResult<String> {
    let request: HyperpathRequest = parse_json(payload)?;
    let table = materialize_hyperpaths(
        &request.lane_id,
        &request.behavior_id,
        &request.candidate_event_table,
        &request.atlas,
        &request.transport,
        request.intervention_faithfulness,
        request.synergy_score_max,
        request.chart_stability,
        request.geodesic_deviation,
    )
    .map_err(py_value_error)?;
    to_json(&table)
}

#[pyfunction]
fn verify_mechanisms_json(payload: &str) -> PyResult<String> {
    let request: CausalRequest = parse_json(payload)?;
    let result = verify_mechanisms(&request.lane, &request.hyperpaths).map_err(py_value_error)?;
    to_json(&result)
}

#[pyfunction]
fn run_workspace_kernels_json(payload: &str) -> PyResult<String> {
    let request: WorkspaceKernelInput = parse_json(payload)?;
    let output =
        execute_workspace_kernels(request).map_err(pyo3::exceptions::PyRuntimeError::new_err)?;
    to_json(&output)
}

#[pyfunction]
fn run_workspace_bundle_json(payload: &str) -> PyResult<String> {
    let request: WorkspaceKernelInput = parse_json(payload)?;
    let output =
        execute_workspace_bundle(request).map_err(pyo3::exceptions::PyRuntimeError::new_err)?;
    to_json(&output)
}

#[pyfunction]
fn run_benchmark_hook(run_id: &str, trace_id: &str) -> PyResult<String> {
    let (_graph, bundle) = geoclt_runtime::run::execute_batch_graph(run_id, trace_id)
        .map_err(pyo3::exceptions::PyRuntimeError::new_err)?;
    Ok(bundle.bundle_hash)
}

pub fn register_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(native_version, m)?)?;
    m.add_function(wrap_pyfunction!(canonical_hash, m)?)?;
    m.add_function(wrap_pyfunction!(validate_json, m)?)?;
    m.add_function(wrap_pyfunction!(fit_atlas_json, m)?)?;
    m.add_function(wrap_pyfunction!(estimate_pullback_metric_json, m)?)?;
    m.add_function(wrap_pyfunction!(fit_transport_json, m)?)?;
    m.add_function(wrap_pyfunction!(propose_events_json, m)?)?;
    m.add_function(wrap_pyfunction!(materialize_hyperpaths_json, m)?)?;
    m.add_function(wrap_pyfunction!(verify_mechanisms_json, m)?)?;
    m.add_function(wrap_pyfunction!(run_workspace_kernels_json, m)?)?;
    m.add_function(wrap_pyfunction!(run_workspace_bundle_json, m)?)?;
    m.add_function(wrap_pyfunction!(run_benchmark_hook, m)?)?;
    Ok(())
}

#[pymodule]
fn geoclt_native(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    register_module(m)
}
