# PROJECT.md

## Project: Geo-CLT

A Rust-first mechanistic-interpretability and mechanism-assurance framework with Python bindings.

This flattened file is the single canonical artifact for the repository. It contains:
- repo purpose
- architectural decisions
- full repo tree
- crate manifests
- Python packaging
- Rust/Python API boundaries
- schema definitions
- sidecar protocol
- benchmark contract hooks
- CLI surface
- test plan
- CI plan
- bootstrap instructions
- minimal Phase 0/1 implementation stubs

The intended workflow is:
1. edit `PROJECT.md`
2. unflatten into repo tree
3. build/test
4. regenerate if needed

---

# 1. Vision

Geo-CLT is a Rust-core system with Python bindings for discovering, validating, and benchmarking chart-consistent causal hyperedge events and canonical mechanism hyperpaths in transformer models.

The system is organized around four principles:

1. Rust owns deterministic schemas, kernels, validation, benchmarking, and runtime guarantees.
2. Python owns model hooks, orchestration, notebooks, and user ergonomics.
3. The scientific object is not a feature or a dyadic edge, but a chart-consistent causal hyperedge event.
4. A mechanism is admitted only if it satisfies causal efficacy, higher-order synergy, chart stability, and transport coherence.

---

# 2. Product phases supported by this repo

## Phase 0: Proof of concept
- one model
- one block pair
- one task profile
- offline benchmark runner
- artifact export
- no sidecar required

## Phase 1: MVP
- reusable workspace
- baseline runner
- artifact validation
- Python SDK
- CLI
- light report generation

## Phase 2: Framework
- canonical schemas
- model adapters
- sidecar runtime
- benchmark lanes
- conformance enforcement

## Phase 3: Product surfaces
- workspace UI
- mechanism explorer
- mechanism differential analysis
- decision receipts
- runtime gating

This repo layout is designed so Phase 0 and Phase 1 are immediately implementable, while Phase 2 and 3 expand without restructuring the core.

---

# 3. Repository tree

```text
geo-clt/
├── PROJECT.md
├── README.md
├── LICENSE
├── .gitignore
├── Cargo.toml
├── Cargo.lock
├── pyproject.toml
├── rust-toolchain.toml
├── justfile
├── Makefile
├── clippy.toml
├── .github/
│   └── workflows/
│       ├── ci-rust.yml
│       ├── ci-python.yml
│       ├── wheels.yml
│       └── release.yml
├── docs/
│   ├── architecture/
│   │   ├── ontology.md
│   │   ├── benchmark-spec.md
│   │   ├── sidecar-protocol.md
│   │   └── artifact-schemas.md
│   ├── guides/
│   │   ├── quickstart-python.md
│   │   ├── quickstart-cli.md
│   │   └── adding-a-benchmark-lane.md
│   └── adr/
│       ├── 0001-rust-core-python-bindings.md
│       ├── 0002-canonical-ir.md
│       └── 0003-sidecar-first-runtime.md
├── schemas/
│   ├── event_record.schema.json
│   ├── hyperpath_record.schema.json
│   ├── mechanism_class_record.schema.json
│   ├── benchmark_result.schema.json
│   ├── decision_receipt.schema.json
│   └── benchmark_lane.schema.json
├── proto/
│   ├── sidecar.proto
│   ├── benchmark.proto
│   └── artifact.proto
├── benches/
│   ├── rust/
│   │   ├── hypergraph_kernels.rs
│   │   ├── transport.rs
│   │   └── metric_patch.rs
│   └── python/
│       ├── benchmark_runner.py
│       └── end_to_end_profile.py
├── examples/
│   ├── configs/
│   │   ├── factual_retrieval.toml
│   │   ├── qwen3_profile.toml
│   │   └── claims_triage.toml
│   └── python/
│       ├── factual_retrieval_poc.py
│       ├── compare_baselines.py
│       ├── inspect_workspace.py
│       └── export_decision_receipt.py
├── data/
│   ├── fixtures/
│   ├── sample_prompts/
│   └── golden/
├── crates/
│   ├── geoclt-core/
│   ├── geoclt-ids/
│   ├── geoclt-units/
│   ├── geoclt-schema/
│   ├── geoclt-artifacts/
│   ├── geoclt-atlas/
│   ├── geoclt-metric/
│   ├── geoclt-transport/
│   ├── geoclt-hypergraph/
│   ├── geoclt-causal/
│   ├── geoclt-canonicalize/
│   ├── geoclt-benchmark/
│   ├── geoclt-sidecar/
│   ├── geoclt-runtime/
│   ├── geoclt-ffi/
│   └── geoclt-cli/
├── bindings/
│   └── python/
│       ├── Cargo.toml
│       └── src/
│           ├── lib.rs
│           ├── errors.rs
│           ├── artifacts.rs
│           ├── benchmark.rs
│           ├── workspace.rs
│           └── sidecar.rs
├── python/
│   ├── geoclt/
│   │   ├── __init__.py
│   │   ├── workspace.py
│   │   ├── profiles.py
│   │   ├── atlas.py
│   │   ├── metric.py
│   │   ├── transport.py
│   │   ├── hypergraph.py
│   │   ├── causal.py
│   │   ├── benchmark.py
│   │   ├── receipts.py
│   │   ├── artifacts.py
│   │   ├── sidecar.py
│   │   ├── plotting.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── transformers.py
│   │   │   ├── vllm.py
│   │   │   └── llama_cpp.py
│   │   └── py.typed
│   ├── notebooks/
│   │   ├── 01_poc.ipynb
│   │   ├── 02_compare_baselines.ipynb
│   │   └── 03_mechanism_explorer.ipynb
│   └── tests/
│       ├── test_workspace.py
│       ├── test_benchmark.py
│       ├── test_artifacts.py
│       └── test_receipts.py
├── services/
│   ├── sidecar/
│   │   ├── Dockerfile
│   │   ├── README.md
│   │   └── config/default.toml
│   ├── api/
│   │   ├── Dockerfile
│   │   └── README.md
│   └── ui/
│       ├── package.json
│       └── README.md
├── scripts/
│   ├── build_wheels.sh
│   ├── run_poc.sh
│   ├── run_sidecar_local.sh
│   ├── validate_artifacts.sh
│   └── release.sh
└── tests/
    ├── integration/
    │   ├── poc_profile.rs
    │   ├── sidecar_roundtrip.rs
    │   ├── benchmark_conformance.rs
    │   └── python_roundtrip.py
    ├── fixtures/
    └── golden/
```

---

# 4. Workspace architecture

## Layer 1: Rust evidence plane
Rust crates own:
- canonical IDs
- typed schemas
- metric kernels
- transport kernels
- hypergraph/event structures
- causal verification kernels
- canonicalization
- benchmark enforcement
- sidecar runtime
- artifact hashing and validation

## Layer 2: Python control plane
Python owns:
- model adapters
- activation capture
- experiment orchestration
- benchmark invocation
- workspace state
- plotting
- notebook UX
- report export

## Layer 3: optional product plane
Services own:
- API server
- sidecar container
- UI
- decision receipt exposure
- runtime routing

---

# 5. Cargo workspace manifest

## File: `Cargo.toml`
```toml
[workspace]
members = [
  "crates/geoclt-core",
  "crates/geoclt-ids",
  "crates/geoclt-units",
  "crates/geoclt-schema",
  "crates/geoclt-artifacts",
  "crates/geoclt-atlas",
  "crates/geoclt-metric",
  "crates/geoclt-transport",
  "crates/geoclt-hypergraph",
  "crates/geoclt-causal",
  "crates/geoclt-canonicalize",
  "crates/geoclt-benchmark",
  "crates/geoclt-sidecar",
  "crates/geoclt-runtime",
  "crates/geoclt-ffi",
  "crates/geoclt-cli",
  "bindings/python",
]
resolver = "2"

[workspace.package]
version = "0.1.0"
edition = "2021"
license = "MIT"
authors = ["Geo-CLT Contributors"]
rust-version = "1.81"

[workspace.dependencies]
anyhow = "1"
thiserror = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
indexmap = { version = "2", features = ["serde"] }
smallvec = "1"
bytes = "1"
uuid = { version = "1", features = ["v5", "serde"] }
sha2 = "0.10"
chrono = { version = "0.4", features = ["serde"] }
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["fmt", "env-filter"] }
clap = { version = "4", features = ["derive"] }
pyo3 = { version = "0.22", features = ["extension-module", "abi3-py310"] }
numpy = "0.22"
pyo3-serde = "0.1"
prost = "0.13"
tonic = "0.12"
tokio = { version = "1", features = ["rt-multi-thread", "macros", "sync", "fs"] }
jsonschema = "0.18"
```

---

# 6. Python packaging

## File: `pyproject.toml`
```toml
[build-system]
requires = ["maturin>=1.7,<2.0"]
build-backend = "maturin"

[project]
name = "geoclt"
version = "0.1.0"
description = "Geo-CLT workspace and Python bindings"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
  { name = "Geo-CLT Contributors" }
]
dependencies = [
  "numpy>=1.26",
  "pydantic>=2.7",
  "pyarrow>=17",
  "networkx>=3.3",
  "rich>=13.7",
  "typer>=0.12",
  "tomli>=2.0; python_version < '3.11'",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3",
  "pytest-cov>=5.0",
  "mypy>=1.11",
  "ruff>=0.6",
  "ipykernel>=6.29",
]

[tool.maturin]
python-source = "python"
module-name = "geoclt_native"
features = ["pyo3/extension-module"]

[tool.pytest.ini_options]
testpaths = ["python/tests"]

[tool.ruff]
line-length = 100

[tool.mypy]
python_version = "3.10"
strict = true
```

---

# 7. Root toolchain and helpers

## File: `rust-toolchain.toml`
```toml
[toolchain]
channel = "1.81.0"
components = ["clippy", "rustfmt"]
profile = "minimal"
```

## File: `justfile`
```make
set shell := ["bash", "-cu"]

build-rust:
    cargo build --workspace

build-python:
    maturin develop

test-rust:
    cargo test --workspace

test-python:
    pytest python/tests -q

lint-rust:
    cargo clippy --workspace --all-targets -- -D warnings

lint-python:
    ruff check python
    mypy python/geoclt

poc:
    python examples/python/factual_retrieval_poc.py

validate-artifacts:
    bash scripts/validate_artifacts.sh
```

## File: `Makefile`
```make
.PHONY: all build test lint poc

all: build test

build:
	cargo build --workspace
	maturin develop

test:
	cargo test --workspace
	pytest python/tests -q

lint:
	cargo clippy --workspace --all-targets -- -D warnings
	ruff check python
	mypy python/geoclt

poc:
	python examples/python/factual_retrieval_poc.py
```

---

# 8. Crate responsibilities

## `geoclt-core`
Purpose: shared traits, errors, and trait boundaries.

### File: `crates/geoclt-core/Cargo.toml`
```toml
[package]
name = "geoclt-core"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
anyhow.workspace = true
thiserror.workspace = true
serde.workspace = true
```

### File: `crates/geoclt-core/src/lib.rs`
```rust
pub mod error;
pub mod traits;
```

### File: `crates/geoclt-core/src/error.rs`
```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum GeoCltError {
    #[error("validation error: {0}")]
    Validation(String),
    #[error("not found: {0}")]
    NotFound(String),
    #[error("unsupported: {0}")]
    Unsupported(String),
}
```

### File: `crates/geoclt-core/src/traits.rs`
```rust
pub trait Validate {
    fn validate(&self) -> Result<(), String>;
}

pub trait StableHash {
    fn stable_hash(&self) -> String;
}
```

---

## `geoclt-ids`
Purpose: deterministic identifiers.

### File: `crates/geoclt-ids/Cargo.toml`
```toml
[package]
name = "geoclt-ids"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
serde.workspace = true
uuid.workspace = true
sha2.workspace = true
```

### File: `crates/geoclt-ids/src/lib.rs`
```rust
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub struct StableId(pub String);

impl StableId {
    pub fn from_parts(parts: &[&str]) -> Self {
        let mut hasher = Sha256::new();
        for p in parts {
            hasher.update(p.as_bytes());
            hasher.update([0u8]);
        }
        let bytes = hasher.finalize();
        Self(format!("{:x}", bytes))
    }
}
```

---

## `geoclt-units`
Purpose: typed scores and indices.

### File: `crates/geoclt-units/Cargo.toml`
```toml
[package]
name = "geoclt-units"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
serde.workspace = true
```

### File: `crates/geoclt-units/src/lib.rs`
```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub struct LayerIndex(pub u32);

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub struct TokenIndex(pub i32);

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct Score(pub f64);
```

---

## `geoclt-schema`
Purpose: canonical IR objects.

### File: `crates/geoclt-schema/Cargo.toml`
```toml
[package]
name = "geoclt-schema"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
serde.workspace = true
indexmap.workspace = true
chrono.workspace = true
geoclt-core = { path = "../geoclt-core" }
geoclt-ids = { path = "../geoclt-ids" }
geoclt-units = { path = "../geoclt-units" }
```

### File: `crates/geoclt-schema/src/lib.rs`
```rust
pub mod benchmark;
pub mod event;
pub mod hyperpath;
pub mod mechanism;
pub mod receipt;
```

### File: `crates/geoclt-schema/src/event.rs`
```rust
use serde::{Deserialize, Serialize};
use geoclt_ids::StableId;
use geoclt_units::Score;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventRecord {
    pub event_id: StableId,
    pub sample_id: String,
    pub layer_span: Vec<u32>,
    pub time_window: String,
    pub participant_set: Vec<String>,
    pub participant_types: Vec<String>,
    pub transport_context_id: Option<String>,
    pub causal_weight: Score,
    pub reliability_score: Score,
    pub proposer_score: Option<Score>,
}
```

### File: `crates/geoclt-schema/src/hyperpath.rs`
```rust
use serde::{Deserialize, Serialize};
use geoclt_ids::StableId;
use geoclt_units::Score;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HyperpathRecord {
    pub path_id: StableId,
    pub behavior_id: String,
    pub event_ids: Vec<StableId>,
    pub chart_ids: Vec<String>,
    pub layer_ids: Vec<u32>,
    pub transport_edge_ids: Vec<String>,
    pub geodesic_deviation: Option<Score>,
    pub chart_stability: Score,
    pub transport_coherence: Score,
    pub intervention_faithfulness: Score,
    pub synergy_score_max: Score,
    pub admitted: bool,
}
```

### File: `crates/geoclt-schema/src/mechanism.rs`
```rust
use serde::{Deserialize, Serialize};
use geoclt_ids::StableId;
use geoclt_units::Score;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MechanismClassRecord {
    pub mechanism_class_id: StableId,
    pub member_path_ids: Vec<StableId>,
    pub atlas_variants_tested: Vec<String>,
    pub persistence_score: Score,
    pub minimality_score: Option<Score>,
    pub geometry_predictiveness: Option<Score>,
    pub pass_fail_status: String,
}
```

### File: `crates/geoclt-schema/src/benchmark.rs`
```rust
use serde::{Deserialize, Serialize};
use geoclt_units::Score;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BenchmarkResult {
    pub run_id: String,
    pub model_id: String,
    pub task_id: String,
    pub baseline_id: String,
    pub metric_name: String,
    pub metric_value: Score,
    pub threshold: Option<Score>,
    pub passed: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BenchmarkLane {
    pub lane_id: String,
    pub behavior_id: String,
    pub intervention_delta_threshold: f64,
    pub synergy_threshold: f64,
    pub chart_stability_threshold: f64,
    pub transport_coherence_threshold: f64,
    pub baseline_margin_threshold: f64,
}
```

### File: `crates/geoclt-schema/src/receipt.rs`
```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecisionReceipt {
    pub receipt_id: String,
    pub input_hash: String,
    pub output_hash: String,
    pub active_mechanism_class_ids: Vec<String>,
    pub provisional_mechanism_class_ids: Vec<String>,
    pub policy_clauses_triggered: Vec<String>,
    pub geometry_anomaly_flags: Vec<String>,
    pub chart_instability_flags: Vec<String>,
    pub decision: String,
}
```

---

## `geoclt-artifacts`
Purpose: serialization, schema validation, hashing.

### File: `crates/geoclt-artifacts/Cargo.toml`
```toml
[package]
name = "geoclt-artifacts"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
serde.workspace = true
serde_json.workspace = true
jsonschema.workspace = true
sha2.workspace = true
geoclt-schema = { path = "../geoclt-schema" }
```

### File: `crates/geoclt-artifacts/src/lib.rs`
```rust
pub mod io;
pub mod validate;
```

### File: `crates/geoclt-artifacts/src/io.rs`
```rust
use serde::Serialize;

pub fn to_pretty_json<T: Serialize>(value: &T) -> Result<String, serde_json::Error> {
    serde_json::to_string_pretty(value)
}
```

### File: `crates/geoclt-artifacts/src/validate.rs`
```rust
pub fn validate_json_against_schema(_instance: &str, _schema: &str) -> Result<(), String> {
    Ok(())
}
```

---

## `geoclt-atlas`
Purpose: chart assignment and atlas support.

### File: `crates/geoclt-atlas/Cargo.toml`
```toml
[package]
name = "geoclt-atlas"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
serde.workspace = true
geoclt-schema = { path = "../geoclt-schema" }
```

### File: `crates/geoclt-atlas/src/lib.rs`
```rust
pub mod atlas;
```

### File: `crates/geoclt-atlas/src/atlas.rs`
```rust
#[derive(Debug, Clone)]
pub struct AtlasSummary {
    pub chart_count: usize,
    pub overlap_score: f64,
}

pub fn summarize_atlas(chart_count: usize, overlap_score: f64) -> AtlasSummary {
    AtlasSummary { chart_count, overlap_score }
}
```

---

## `geoclt-metric`
Purpose: metric patches and geometric summaries.

### File: `crates/geoclt-metric/Cargo.toml`
```toml
[package]
name = "geoclt-metric"
version.workspace = true
edition.workspace = true
license.workspace = true
```

### File: `crates/geoclt-metric/src/lib.rs`
```rust
pub mod metric;
```

### File: `crates/geoclt-metric/src/metric.rs`
```rust
#[derive(Debug, Clone)]
pub struct MetricPatch {
    pub chart_id: String,
    pub curvature_summary: f64,
    pub distortion_score: f64,
}
```

---

## `geoclt-transport`
Purpose: transport operators and diagnostics.

### File: `crates/geoclt-transport/Cargo.toml`
```toml
[package]
name = "geoclt-transport"
version.workspace = true
edition.workspace = true
license.workspace = true
```

### File: `crates/geoclt-transport/src/lib.rs`
```rust
pub mod transport;
```

### File: `crates/geoclt-transport/src/transport.rs`
```rust
#[derive(Debug, Clone)]
pub struct TransportDiagnostics {
    pub loop_consistency: f64,
    pub distortion: f64,
    pub coherence: f64,
}
```

---

## `geoclt-hypergraph`
Purpose: higher-order event structures.

### File: `crates/geoclt-hypergraph/Cargo.toml`
```toml
[package]
name = "geoclt-hypergraph"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
geoclt-schema = { path = "../geoclt-schema" }
```

### File: `crates/geoclt-hypergraph/src/lib.rs`
```rust
pub mod induce;
```

### File: `crates/geoclt-hypergraph/src/induce.rs`
```rust
use geoclt_schema::event::EventRecord;

pub fn propose_events(events: Vec<EventRecord>) -> Vec<EventRecord> {
    events
}
```

---

## `geoclt-causal`
Purpose: STII-style validation and subset ablation support.

### File: `crates/geoclt-causal/Cargo.toml`
```toml
[package]
name = "geoclt-causal"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
geoclt-schema = { path = "../geoclt-schema" }
```

### File: `crates/geoclt-causal/src/lib.rs`
```rust
pub mod verify;
```

### File: `crates/geoclt-causal/src/verify.rs`
```rust
#[derive(Debug, Clone)]
pub struct VerificationResult {
    pub causal_delta: f64,
    pub synergy: f64,
    pub passed: bool,
}

pub fn verify(causal_delta: f64, synergy: f64, delta_threshold: f64, synergy_threshold: f64) -> VerificationResult {
    VerificationResult {
        causal_delta,
        synergy,
        passed: causal_delta >= delta_threshold && synergy >= synergy_threshold,
    }
}
```

---

## `geoclt-canonicalize`
Purpose: reconcile mechanism identity across atlas variants.

### File: `crates/geoclt-canonicalize/Cargo.toml`
```toml
[package]
name = "geoclt-canonicalize"
version.workspace = true
edition.workspace = true
license.workspace = true
```

### File: `crates/geoclt-canonicalize/src/lib.rs`
```rust
pub mod canonicalize;
```

### File: `crates/geoclt-canonicalize/src/canonicalize.rs`
```rust
pub fn canonical_mechanism_key(parts: &[&str]) -> String {
    parts.join("::")
}
```

---

## `geoclt-benchmark`
Purpose: admission rule, falsifiers, baseline comparisons.

### File: `crates/geoclt-benchmark/Cargo.toml`
```toml
[package]
name = "geoclt-benchmark"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
geoclt-schema = { path = "../geoclt-schema" }
geoclt-causal = { path = "../geoclt-causal" }
```

### File: `crates/geoclt-benchmark/src/lib.rs`
```rust
pub mod admission;
pub mod falsifiers;
```

### File: `crates/geoclt-benchmark/src/admission.rs`
```rust
use geoclt_schema::hyperpath::HyperpathRecord;
use geoclt_schema::benchmark::BenchmarkLane;

pub fn admitted(path: &HyperpathRecord, lane: &BenchmarkLane) -> bool {
    path.intervention_faithfulness.0 >= lane.intervention_delta_threshold
        && path.synergy_score_max.0 >= lane.synergy_threshold
        && path.chart_stability.0 >= lane.chart_stability_threshold
        && path.transport_coherence.0 >= lane.transport_coherence_threshold
}
```

### File: `crates/geoclt-benchmark/src/falsifiers.rs`
```rust
#[derive(Debug, Clone)]
pub struct FalsifierReport {
    pub pairwise_sufficiency_triggered: bool,
    pub chart_fragility_triggered: bool,
    pub transport_irrelevance_triggered: bool,
    pub geometry_non_predictiveness_triggered: bool,
    pub spurious_synergy_triggered: bool,
}
```

---

## `geoclt-sidecar`
Purpose: sidecar runtime.

### File: `crates/geoclt-sidecar/Cargo.toml`
```toml
[package]
name = "geoclt-sidecar"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
tokio.workspace = true
tonic.workspace = true
prost.workspace = true
```

### File: `crates/geoclt-sidecar/src/lib.rs`
```rust
pub mod server;
```

### File: `crates/geoclt-sidecar/src/server.rs`
```rust
pub async fn serve(_addr: &str) -> Result<(), Box<dyn std::error::Error>> {
    Ok(())
}
```

---

## `geoclt-runtime`
Purpose: end-to-end orchestration in Rust.

### File: `crates/geoclt-runtime/Cargo.toml`
```toml
[package]
name = "geoclt-runtime"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
geoclt-benchmark = { path = "../geoclt-benchmark" }
geoclt-artifacts = { path = "../geoclt-artifacts" }
geoclt-schema = { path = "../geoclt-schema" }
```

### File: `crates/geoclt-runtime/src/lib.rs`
```rust
pub mod run;
```

### File: `crates/geoclt-runtime/src/run.rs`
```rust
use geoclt_schema::benchmark::BenchmarkLane;
use geoclt_schema::hyperpath::HyperpathRecord;
use geoclt_benchmark::admission::admitted;

pub fn evaluate_path(path: &HyperpathRecord, lane: &BenchmarkLane) -> bool {
    admitted(path, lane)
}
```

---

## `geoclt-ffi`
Purpose: stable Rust API surfaced to Python.

### File: `crates/geoclt-ffi/Cargo.toml`
```toml
[package]
name = "geoclt-ffi"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
pyo3.workspace = true
serde_json.workspace = true
geoclt-runtime = { path = "../geoclt-runtime" }
geoclt-schema = { path = "../geoclt-schema" }
```

### File: `crates/geoclt-ffi/src/lib.rs`
```rust
use pyo3::prelude::*;

#[pyfunction]
fn native_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

#[pymodule]
fn geoclt_native(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(native_version, m)?)?;
    Ok(())
}
```

---

## `geoclt-cli`
Purpose: command-line entrypoints.

### File: `crates/geoclt-cli/Cargo.toml`
```toml
[package]
name = "geoclt-cli"
version.workspace = true
edition.workspace = true
license.workspace = true

[dependencies]
clap.workspace = true
anyhow.workspace = true
```

### File: `crates/geoclt-cli/src/main.rs`
```rust
use clap::{Parser, Subcommand};

#[derive(Parser)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Version,
    ValidateArtifacts,
}

fn main() {
    let cli = Cli::parse();
    match cli.command {
        Commands::Version => println!("0.1.0"),
        Commands::ValidateArtifacts => println!("ok"),
    }
}
```

---

# 9. Python bindings crate

## File: `bindings/python/Cargo.toml`
```toml
[package]
name = "geoclt-python-bindings"
version.workspace = true
edition.workspace = true
license.workspace = true

[lib]
name = "geoclt_native"
crate-type = ["cdylib"]

[dependencies]
pyo3.workspace = true
geoclt-ffi = { path = "../../crates/geoclt-ffi" }
```

## File: `bindings/python/src/lib.rs`
```rust
pub use geoclt_ffi::*;
```

## File: `bindings/python/src/errors.rs`
```rust
// reserved for richer Python exception mapping
```

## File: `bindings/python/src/artifacts.rs`
```rust
// reserved for Python-facing artifact helpers
```

## File: `bindings/python/src/benchmark.rs`
```rust
// reserved for Python-facing benchmark helpers
```

## File: `bindings/python/src/workspace.rs`
```rust
// reserved for Python-facing workspace helpers
```

## File: `bindings/python/src/sidecar.rs`
```rust
// reserved for Python-facing sidecar helpers
```

---

# 10. Python package contents

## File: `python/geoclt/__init__.py`
```python
from .workspace import Workspace
from .profiles import BenchmarkLaneConfig

__all__ = ["Workspace", "BenchmarkLaneConfig"]
```

## File: `python/geoclt/profiles.py`
```python
from dataclasses import dataclass


@dataclass(slots=True)
class BenchmarkLaneConfig:
    lane_id: str
    behavior_id: str
    intervention_delta_threshold: float = 0.10
    synergy_threshold: float = 0.05
    chart_stability_threshold: float = 0.70
    transport_coherence_threshold: float = 0.70
    baseline_margin_threshold: float = 0.05
```

## File: `python/geoclt/workspace.py`
```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .profiles import BenchmarkLaneConfig


@dataclass
class Workspace:
    root: Path
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, path: str | Path) -> "Workspace":
        root = Path(path)
        root.mkdir(parents=True, exist_ok=True)
        return cls(root=root)

    def attach_model(self, model: Any) -> None:
        self.metadata["model"] = repr(model)

    def fit_atlas(self, profile: str) -> None:
        self.metadata["atlas_profile"] = profile

    def fit_transport(self) -> None:
        self.metadata["transport"] = "fit"

    def propose_events(self) -> None:
        self.metadata["events"] = "proposed"

    def verify_mechanisms(self) -> None:
        self.metadata["mechanisms"] = "verified"

    def run_benchmark(self, lane: BenchmarkLaneConfig) -> dict[str, Any]:
        return {
            "lane_id": lane.lane_id,
            "status": "completed",
            "metadata": self.metadata,
        }
```

## File: `python/geoclt/atlas.py`
```python
def fit_atlas(*args, **kwargs):
    return {"status": "ok", "component": "atlas"}
```

## File: `python/geoclt/metric.py`
```python
def estimate_pullback_metric(*args, **kwargs):
    return {"status": "ok", "component": "metric"}
```

## File: `python/geoclt/transport.py`
```python
def fit_transport(*args, **kwargs):
    return {"status": "ok", "component": "transport"}
```

## File: `python/geoclt/hypergraph.py`
```python
def propose_events(*args, **kwargs):
    return {"status": "ok", "component": "hypergraph"}
```

## File: `python/geoclt/causal.py`
```python
def verify_mechanisms(*args, **kwargs):
    return {"status": "ok", "component": "causal"}
```

## File: `python/geoclt/benchmark.py`
```python
def compare_baselines(*args, **kwargs):
    return {"status": "ok", "component": "benchmark"}
```

## File: `python/geoclt/receipts.py`
```python
def emit_decision_receipt(*args, **kwargs):
    return {"status": "ok", "component": "receipt"}
```

## File: `python/geoclt/artifacts.py`
```python
import json
from pathlib import Path
from typing import Any


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
```

## File: `python/geoclt/sidecar.py`
```python
def start_sidecar_local(*args, **kwargs):
    return {"status": "ok", "component": "sidecar"}
```

## File: `python/geoclt/plotting.py`
```python
def plot_placeholder(*args, **kwargs):
    return None
```

## File: `python/geoclt/adapters/__init__.py`
```python
from .transformers import attach_transformers_hooks
```

## File: `python/geoclt/adapters/transformers.py`
```python
def attach_transformers_hooks(model, layers=None):
    return {"model": repr(model), "layers": layers or []}
```

## File: `python/geoclt/adapters/vllm.py`
```python
def attach_vllm_hooks(engine, layers=None):
    return {"engine": repr(engine), "layers": layers or []}
```

## File: `python/geoclt/adapters/llama_cpp.py`
```python
def attach_llama_cpp_hooks(model, layers=None):
    return {"model": repr(model), "layers": layers or []}
```

---

# 11. JSON schemas

## File: `schemas/event_record.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EventRecord",
  "type": "object",
  "required": [
    "event_id",
    "sample_id",
    "layer_span",
    "time_window",
    "participant_set",
    "participant_types",
    "causal_weight",
    "reliability_score"
  ],
  "properties": {
    "event_id": { "type": "string" },
    "sample_id": { "type": "string" },
    "layer_span": { "type": "array", "items": { "type": "integer" } },
    "time_window": { "type": "string" },
    "participant_set": { "type": "array", "items": { "type": "string" } },
    "participant_types": { "type": "array", "items": { "type": "string" } },
    "transport_context_id": { "type": ["string", "null"] },
    "causal_weight": { "type": "number" },
    "reliability_score": { "type": "number" },
    "proposer_score": { "type": ["number", "null"] }
  }
}
```

## File: `schemas/hyperpath_record.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "HyperpathRecord",
  "type": "object",
  "required": [
    "path_id",
    "behavior_id",
    "event_ids",
    "chart_ids",
    "layer_ids",
    "transport_edge_ids",
    "chart_stability",
    "transport_coherence",
    "intervention_faithfulness",
    "synergy_score_max",
    "admitted"
  ],
  "properties": {
    "path_id": { "type": "string" },
    "behavior_id": { "type": "string" },
    "event_ids": { "type": "array", "items": { "type": "string" } },
    "chart_ids": { "type": "array", "items": { "type": "string" } },
    "layer_ids": { "type": "array", "items": { "type": "integer" } },
    "transport_edge_ids": { "type": "array", "items": { "type": "string" } },
    "geodesic_deviation": { "type": ["number", "null"] },
    "chart_stability": { "type": "number" },
    "transport_coherence": { "type": "number" },
    "intervention_faithfulness": { "type": "number" },
    "synergy_score_max": { "type": "number" },
    "admitted": { "type": "boolean" }
  }
}
```

## File: `schemas/mechanism_class_record.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "MechanismClassRecord",
  "type": "object",
  "required": [
    "mechanism_class_id",
    "member_path_ids",
    "atlas_variants_tested",
    "persistence_score",
    "pass_fail_status"
  ],
  "properties": {
    "mechanism_class_id": { "type": "string" },
    "member_path_ids": { "type": "array", "items": { "type": "string" } },
    "atlas_variants_tested": { "type": "array", "items": { "type": "string" } },
    "persistence_score": { "type": "number" },
    "minimality_score": { "type": ["number", "null"] },
    "geometry_predictiveness": { "type": ["number", "null"] },
    "pass_fail_status": { "type": "string" }
  }
}
```

## File: `schemas/benchmark_result.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "BenchmarkResult",
  "type": "object",
  "required": [
    "run_id",
    "model_id",
    "task_id",
    "baseline_id",
    "metric_name",
    "metric_value",
    "passed"
  ],
  "properties": {
    "run_id": { "type": "string" },
    "model_id": { "type": "string" },
    "task_id": { "type": "string" },
    "baseline_id": { "type": "string" },
    "metric_name": { "type": "string" },
    "metric_value": { "type": "number" },
    "threshold": { "type": ["number", "null"] },
    "passed": { "type": "boolean" }
  }
}
```

## File: `schemas/decision_receipt.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DecisionReceipt",
  "type": "object",
  "required": [
    "receipt_id",
    "input_hash",
    "output_hash",
    "active_mechanism_class_ids",
    "provisional_mechanism_class_ids",
    "policy_clauses_triggered",
    "geometry_anomaly_flags",
    "chart_instability_flags",
    "decision"
  ],
  "properties": {
    "receipt_id": { "type": "string" },
    "input_hash": { "type": "string" },
    "output_hash": { "type": "string" },
    "active_mechanism_class_ids": { "type": "array", "items": { "type": "string" } },
    "provisional_mechanism_class_ids": { "type": "array", "items": { "type": "string" } },
    "policy_clauses_triggered": { "type": "array", "items": { "type": "string" } },
    "geometry_anomaly_flags": { "type": "array", "items": { "type": "string" } },
    "chart_instability_flags": { "type": "array", "items": { "type": "string" } },
    "decision": { "type": "string" }
  }
}
```

## File: `schemas/benchmark_lane.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "BenchmarkLane",
  "type": "object",
  "required": [
    "lane_id",
    "behavior_id",
    "intervention_delta_threshold",
    "synergy_threshold",
    "chart_stability_threshold",
    "transport_coherence_threshold",
    "baseline_margin_threshold"
  ],
  "properties": {
    "lane_id": { "type": "string" },
    "behavior_id": { "type": "string" },
    "intervention_delta_threshold": { "type": "number" },
    "synergy_threshold": { "type": "number" },
    "chart_stability_threshold": { "type": "number" },
    "transport_coherence_threshold": { "type": "number" },
    "baseline_margin_threshold": { "type": "number" }
  }
}
```

---

# 12. Proto definitions

## File: `proto/sidecar.proto`
```proto
syntax = "proto3";

package geoclt.sidecar;

message ActivationChunk {
  string trace_id = 1;
  string model_id = 2;
  uint32 layer_id = 3;
  bytes payload = 4;
}

message Ack {
  bool ok = 1;
  string message = 2;
}

service SidecarService {
  rpc PushActivation(ActivationChunk) returns (Ack);
}
```

## File: `proto/benchmark.proto`
```proto
syntax = "proto3";

package geoclt.benchmark;

message BenchmarkRequest {
  string workspace_id = 1;
  string lane_id = 2;
}

message BenchmarkResponse {
  bool ok = 1;
  string report_path = 2;
}

service BenchmarkService {
  rpc RunBenchmark(BenchmarkRequest) returns (BenchmarkResponse);
}
```

## File: `proto/artifact.proto`
```proto
syntax = "proto3";

package geoclt.artifact;

message ArtifactRef {
  string artifact_id = 1;
  string path = 2;
}
```

---

# 13. Example config

## File: `examples/configs/factual_retrieval.toml`
```toml
lane_id = "factual_retrieval.v1"
behavior_id = "factual_retrieval"
intervention_delta_threshold = 0.10
synergy_threshold = 0.05
chart_stability_threshold = 0.70
transport_coherence_threshold = 0.70
baseline_margin_threshold = 0.05

[model]
model_id = "gpt2-small"
block_pair = [5, 6]
token_position_class = "answer-token"

[atlas]
chart_count = 3

[transport]
enabled = true

[geometry]
mode = "pullback"
```

---

# 14. Example Python scripts

## File: `examples/python/factual_retrieval_poc.py`
```python
from geoclt import Workspace, BenchmarkLaneConfig


def main() -> None:
    ws = Workspace.create("runs/factual-retrieval")
    ws.attach_model("gpt2-small")
    ws.fit_atlas(profile="factual_retrieval")
    ws.fit_transport()
    ws.propose_events()
    ws.verify_mechanisms()
    report = ws.run_benchmark(BenchmarkLaneConfig(
        lane_id="factual_retrieval.v1",
        behavior_id="factual_retrieval",
    ))
    print(report)


if __name__ == "__main__":
    main()
```

## File: `examples/python/compare_baselines.py`
```python
from geoclt.benchmark import compare_baselines

print(compare_baselines())
```

## File: `examples/python/inspect_workspace.py`
```python
from geoclt import Workspace

ws = Workspace.create("runs/demo")
print(ws)
```

## File: `examples/python/export_decision_receipt.py`
```python
from geoclt.receipts import emit_decision_receipt

print(emit_decision_receipt())
```

---

# 15. Tests

## Rust integration tests

### File: `tests/integration/poc_profile.rs`
```rust
#[test]
fn poc_profile_smoke_test() {
    assert_eq!(2 + 2, 4);
}
```

### File: `tests/integration/sidecar_roundtrip.rs`
```rust
#[test]
fn sidecar_roundtrip_placeholder() {
    assert!(true);
}
```

### File: `tests/integration/benchmark_conformance.rs`
```rust
#[test]
fn benchmark_conformance_placeholder() {
    assert!(true);
}
```

## Python tests

### File: `python/tests/test_workspace.py`
```python
from geoclt import Workspace


def test_workspace_create(tmp_path):
    ws = Workspace.create(tmp_path / "ws")
    assert ws.root.exists()
```

### File: `python/tests/test_benchmark.py`
```python
from geoclt import Workspace, BenchmarkLaneConfig


def test_benchmark_run(tmp_path):
    ws = Workspace.create(tmp_path / "ws")
    report = ws.run_benchmark(BenchmarkLaneConfig(
        lane_id="lane",
        behavior_id="behavior",
    ))
    assert report["status"] == "completed"
```

### File: `python/tests/test_artifacts.py`
```python
from geoclt.artifacts import write_json


def test_write_json(tmp_path):
    path = tmp_path / "a.json"
    write_json(path, {"ok": True})
    assert path.exists()
```

### File: `python/tests/test_receipts.py`
```python
from geoclt.receipts import emit_decision_receipt


def test_receipt_smoke():
    out = emit_decision_receipt()
    assert out["status"] == "ok"
```

---

# 16. CI workflows

## File: `.github/workflows/ci-rust.yml`
```yaml
name: ci-rust
on: [push, pull_request]
jobs:
  rust:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo build --workspace
      - run: cargo test --workspace
      - run: cargo clippy --workspace --all-targets -- -D warnings
```

## File: `.github/workflows/ci-python.yml`
```yaml
name: ci-python
on: [push, pull_request]
jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install maturin ruff mypy pytest
      - run: maturin develop
      - run: pytest python/tests -q
      - run: ruff check python
      - run: mypy python/geoclt
```

## File: `.github/workflows/wheels.yml`
```yaml
name: wheels
on:
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: PyO3/maturin-action@v1
        with:
          command: build
```

## File: `.github/workflows/release.yml`
```yaml
name: release
on:
  workflow_dispatch:

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "release placeholder"
```

---

# 17. Scripts

## File: `scripts/build_wheels.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
maturin build
```

## File: `scripts/run_poc.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
python examples/python/factual_retrieval_poc.py
```

## File: `scripts/run_sidecar_local.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
cargo run -p geoclt-cli -- version
```

## File: `scripts/validate_artifacts.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
echo "artifact validation placeholder"
```

## File: `scripts/release.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
echo "release placeholder"
```

---

# 18. README

## File: `README.md`
```md
# Geo-CLT

Geo-CLT is a Rust-core, Python-facing framework for mechanism discovery, mechanism admission, and benchmarked mechanistic assurance.

## Core ideas
- Rust core for deterministic schemas, kernels, validation, sidecar runtime, and benchmark enforcement
- Python workspace for model integration, orchestration, and user ergonomics
- canonical mechanism object: chart-consistent causal hyperedge event
- canonical admitted mechanism: causally necessary, synergistic, chart-stable, transport-coherent hyperpath

## Quickstart
```bash
cargo build --workspace
maturin develop
python examples/python/factual_retrieval_poc.py
```

## Status
- Phase 0/1 starter repo
- Rust core with Python bindings
- benchmark and artifact scaffolding
```

---

# 19. Sidecar service container

## File: `services/sidecar/Dockerfile`
```dockerfile
FROM rust:1.81 as build
WORKDIR /app
COPY . .
RUN cargo build --release -p geoclt-cli

FROM debian:bookworm-slim
COPY --from=build /app/target/release/geoclt-cli /usr/local/bin/geoclt-cli
CMD ["geoclt-cli", "version"]
```

## File: `services/sidecar/config/default.toml`
```toml
bind_addr = "0.0.0.0:50051"
mode = "development"
```

## File: `services/sidecar/README.md`
```md
# Sidecar Service

Reserved for Phase 2 runtime deployment.
```

---

# 20. API and UI placeholders

## File: `services/api/README.md`
```md
# API Service

Reserved for Phase 3 product surface.
```

## File: `services/api/Dockerfile`
```dockerfile
FROM python:3.11-slim
CMD ["python", "-c", "print('api placeholder')"]
```

## File: `services/ui/README.md`
```md
# UI

Reserved for workspace and mechanism explorer UI.
```

## File: `services/ui/package.json`
```json
{
  "name": "geoclt-ui",
  "private": true,
  "version": "0.1.0"
}
```

---

# 21. Docs stubs

## File: `docs/architecture/ontology.md`
```md
# Ontology

Primitive object: chart-consistent causal hyperedge event.
Mechanism: canonical cross-layer hyperpath satisfying admission thresholds.
```

## File: `docs/architecture/benchmark-spec.md`
```md
# Benchmark Spec

See PROJECT.md for current normative thresholds and crate layout.
```

## File: `docs/architecture/sidecar-protocol.md`
```md
# Sidecar Protocol

Primary inference process emits activation chunks to sidecar.
```

## File: `docs/architecture/artifact-schemas.md`
```md
# Artifact Schemas

Canonical JSON schemas live in `/schemas`.
```

---

# 22. Phase-aware implementation priorities

## Phase 0 required files
Required now:
- root workspace files
- `geoclt-core`
- `geoclt-ids`
- `geoclt-units`
- `geoclt-schema`
- `geoclt-atlas`
- `geoclt-metric`
- `geoclt-transport`
- `geoclt-hypergraph`
- `geoclt-causal`
- `geoclt-benchmark`
- `geoclt-ffi`
- Python workspace package
- examples
- tests

## Phase 1 required additions
Add:
- `geoclt-artifacts`
- `geoclt-canonicalize`
- `geoclt-cli`
- richer Python reports
- schema validation enforcement

## Phase 2 additions
Add:
- `geoclt-sidecar`
- `geoclt-runtime`
- proto-generated services
- streaming ingestion

## Phase 3 additions
Add:
- services/api
- services/ui
- decision receipts in production workflows
- runtime policy controls

---

# 23. Benchmark defaults

Default thresholds encoded in both Rust and Python should be:
- intervention delta threshold = `0.10`
- synergy threshold = `0.05`
- chart stability threshold = `0.70`
- transport coherence threshold = `0.70`
- baseline margin threshold = `0.05`

These values are starter defaults for the bounded prototype and must remain lane-configurable.

---

# 24. Public API surface

## Rust CLI
```text
geoclt version
geoclt validate-artifacts
```

## Python SDK
```python
from geoclt import Workspace, BenchmarkLaneConfig

ws = Workspace.create("runs/demo")
ws.attach_model("gpt2-small")
ws.fit_atlas(profile="factual_retrieval")
ws.fit_transport()
ws.propose_events()
ws.verify_mechanisms()
report = ws.run_benchmark(BenchmarkLaneConfig(
    lane_id="factual_retrieval.v1",
    behavior_id="factual_retrieval",
))
```

---

# 25. Non-goals for the initial repo

Not in initial scope:
- distributed training infrastructure
- custom CUDA kernels
- full UI implementation
- full gRPC sidecar implementation
- full benchmark mathematics implementation
- enterprise auth
- multi-tenant storage

This file defines the correct repo shape and stable interfaces first.

---

# 26. Bootstrap sequence

## Local development bootstrap
```bash
cargo build --workspace
maturin develop
pytest python/tests -q
python examples/python/factual_retrieval_poc.py
```

## Minimal success condition
The repository is correctly bootstrapped when:
1. Rust workspace builds
2. Python extension imports
3. tests pass
4. example POC script runs

---

# 27. Canonical naming conventions

- crate prefix: `geoclt-*`
- Python package: `geoclt`
- native extension: `geoclt_native`
- CLI binary: `geoclt-cli`
- artifact records end in `Record`
- lane configs end in `Lane`

---

# 28. Future extension hooks

Reserved extension points:
- alternate metric engines
- alternate canonicalization strategies
- additional model adapters
- additional benchmark lanes
- decision receipt policy packs
- runtime gatekeeper
- mechanism registry service

---

# 29. Final note

This PROJECT.md is the authoritative flattened representation of the repository. The preferred implementation discipline is:
- update this file first
- unflatten into concrete files
- run build/test
- keep all crate and package boundaries synchronized with this document

The repo is intentionally shaped to prove the primitive first, then mechanism admission, then framework reuse, then product capability.

