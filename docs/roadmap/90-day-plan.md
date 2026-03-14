# Geo-CLT 90-Day Plan (Phase 0 -> Phase 1)

Plan window: **March 16, 2026 - June 12, 2026** (13 weeks)

## 1) Objectives and hard boundaries

### Primary objective
By June 12, 2026, deliver:
- Phase 0 proof that at least one canonical hyperpath is causally useful and beats at least one weaker baseline.
- Phase 1 MVP mechanism workbench that another engineer can run end-to-end without notebook edits.

### Non-goals in this 90-day window
- No production runtime gating.
- No enterprise multi-tenancy, RBAC, or compliance packs.
- No broad-model support beyond 2-3 model families.
- No large-scale sidecar deployment (protocol stubs only in this window).

## 2) Staffing and ownership

Minimum team:
- Research Engineer (RE): ontology, experiments, falsifiers, writeups.
- Systems ML Engineer (SMLE): Rust/Python core, artifacts, benchmark engine, CI.
- Optional Frontend Engineer (0.3-0.5 FTE): Explorer UI after Phase 0 gate.

Ownership map:
- RE owns: Phase 0 experiment design, ablation validity, benchmark interpretation.
- SMLE owns: repo contracts, schemas, deterministic artifacts, reproducible runners.
- FE owns: Phase 1 explorer shell, run inspection screens, report UX.

## 3) Repo layout contract for Phase 0/1

Must exist and stay stable through day 90:
- Rust core crates under `crates/geoclt-*`.
- Python control plane under `python/geoclt/`.
- Canonical schemas under `schemas/`.
- Benchmarks and runnable examples under `benches/` and `examples/`.
- Integration checks under `tests/integration/` and `python/tests/`.

Must not churn after Week 4 without ADR:
- `EventRecord`, `HyperpathRecord`, `BenchmarkResult` shape.
- Benchmark lane thresholds and falsifier naming.
- Public Python entrypoint shape (`Workspace` + benchmark lane config).

## 4) Week-by-week milestones

## Week 1 (March 16-20, 2026)
- Lock Phase 0 benchmark spec and falsifier definitions.
- Finalize crate dependency direction and Python API boundaries.
- Establish CI baseline: Rust build/test/lint + Python test/lint/mypy.
- Deliverable: architecture freeze memo + runnable scaffold in CI.

## Week 2 (March 23-27, 2026)
- Implement deterministic IDs and canonical schema validation path.
- Add artifact writer/loader primitives (JSON now; parquet deferred).
- Define one factual-retrieval lane config and baseline registry.
- Deliverable: schema-conformant artifact smoke test.

## Week 3 (March 30-April 3, 2026)
- Build activation capture path for one model + one block pair.
- Add minimal dataset/profile loader for bounded prototype.
- Wire first offline pipeline command/notebook path.
- Deliverable: raw activation capture reproducible from clean checkout.

## Week 4 (April 6-10, 2026)
- Add small SAE atlas workflow and overlap summary.
- Add local pullback metric estimation primitive.
- Emit atlas overlap + metric patch artifacts.
- Deliverable: first two benchmark outputs generated automatically.

## Week 5 (April 13-17, 2026)
- Implement one geometric CLT transport between adjacent layers.
- Emit transport diagnostics and coherence metrics.
- Add geometry-free and pairwise baseline runs.
- Deliverable: transport error report + baseline comparisons.

## Week 6 (April 20-24, 2026)
- Implement candidate hyperedge proposal over features/heads/gates.
- Add STII-style synergy scoring and subset ablation runner.
- Emit candidate event table and ablation outcomes.
- Deliverable: candidate event table (benchmark output #3).

## Week 7 (April 27-May 1, 2026)
- Implement canonical hyperpath assembly + admission predicate.
- Add chart substitution stability checks across seeds.
- Emit admitted hyperpath table + falsifier sheet.
- Deliverable: all five Phase 0 benchmark outputs generated.

## Week 8 (May 4-8, 2026)
- Run Phase 0 evaluation pass with required baselines.
- Publish Phase 0 report (passed + failed falsifiers, risks, caveats).
- Go/No-Go checkpoint for Phase 1.
- Deliverable: signed Phase 0 decision packet.

## Week 9 (May 11-15, 2026)
- Build Python `Workspace` lifecycle for repeatable non-notebook runs.
- Add run registry metadata (SQLite acceptable for MVP).
- Stabilize benchmark lane invocation API.
- Deliverable: run -> inspect -> export flow from CLI/SDK.

## Week 10 (May 18-22, 2026)
- Build baseline runner abstraction and report serializer.
- Add mechanism candidate/admitted views in Python surface.
- Add first Mechanism Explorer page skeleton.
- Deliverable: internal user can compare baseline outputs in one command.

## Week 11 (May 25-29, 2026)
- Implement benchmark contract engine (threshold + falsifier + conformance labels).
- Add decision artifact export bundle for each run.
- Harden tests for contract regressions.
- Deliverable: conformance classification from canonical artifacts.

## Week 12 (June 1-5, 2026)
- Expand model/task coverage to 2-3 x 2-3 matrix (bounded lanes only).
- Improve UX for run inspection and export.
- Run reproducibility pass from clean environment.
- Deliverable: reproducibility checklist completed by non-author engineer.

## Week 13 (June 8-12, 2026)
- Phase 1 stabilization sprint: docs, CI reliability, packaging polish.
- Ship MVP release candidate (`v0.1.0-rc1` internal).
- Formal Phase 1 go/no-go review.
- Deliverable: internal MVP handoff + next-phase backlog.

## 5) Go/No-Go criteria

### Phase 0 gate (Week 8, May 8, 2026)
Go if all are true:
- At least one admitted hyperpath satisfies causal efficacy, higher-order synergy, chart stability, and transport coherence.
- At least one weaker baseline is beaten on intervention faithfulness.
- Five benchmark outputs are reproducible from clean checkout.
- At least one falsifier fails somewhere (proves kill logic is active).

No-Go if any are true:
- Pairwise baselines match intervention faithfulness within noise.
- Chart stability collapses across seeds.
- Geometry-aware variant shows no measurable lift.
- STII-positive events fail direct subset ablations.

Actions on No-Go:
- 2-week scope reduction: collapse ontology depth, narrow behavior/task, re-test primitive.
- Freeze UI work until primitive recovers.

### Phase 1 gate (Week 13, June 12, 2026)
Go if all are true:
- A non-author engineer runs profile -> benchmark -> inspect -> export without notebook edits.
- Benchmark contract engine produces deterministic conformance classes.
- Baseline runner covers at least four baselines.
- Artifact bundle validates against schema checks in CI.

No-Go if any are true:
- Pipeline requires manual notebook surgery.
- Conformance outputs drift for identical inputs.
- Baseline comparisons are incomplete or non-repeatable.

Actions on No-Go:
- 2-week hardening sprint focused on reproducibility and contract determinism.

## 6) KPI dashboard (tracked weekly)

Scientific validity KPIs:
- `% admitted hyperpaths passing all four admission tests`.
- `delta(intervention_faithfulness) vs strongest baseline`.
- `chart stability variance across seeds`.
- `falsifier trigger rate by lane`.

Engineering KPIs:
- clean-run success rate in CI.
- median runtime per lane.
- artifact schema validation pass rate.
- ratio of deterministic reruns (same input -> same artifact hash).

Usability KPIs (Phase 1 onward):
- time for non-author to run first lane.
- number of manual steps outside SDK/CLI.
- export success rate for benchmark reports.

## 7) Risk register with mitigations

Risk: ontology complexity outruns evidence.
- Mitigation: enforce Phase 0 kill criteria; no Phase 1 expansion without gate pass.

Risk: schema churn breaks reproducibility.
- Mitigation: ADR requirement after Week 4 for schema contract changes.

Risk: Python and Rust surfaces diverge.
- Mitigation: bind only stable domain actions; add cross-language integration tests.

Risk: UI consumes core bandwidth too early.
- Mitigation: FE work starts only after Week 8 Go.

## 8) Decision cadence

Cadence:
- Weekly engineering review every Friday.
- Biweekly scientific validity review (RE + SMLE).
- Formal gate reviews: May 8, 2026 and June 12, 2026.

Required artifacts at each gate:
- benchmark output bundle,
- falsifier summary,
- reproducibility log,
- decision memo (go/no-go + rationale).

## 9) Immediate next 10 working days (execution checklist)

1. Freeze benchmark lane spec and falsifier list in docs.
2. Add contract tests for `EventRecord` / `HyperpathRecord` / `BenchmarkResult`.
3. Wire deterministic artifact hashing in Rust.
4. Implement single-model activation capture path.
5. Add baseline registry and runner skeleton.
6. Add CLI command for profile run.
7. Add Python `Workspace.run_benchmark(...)` end-to-end integration test.
8. Add CI check that reruns one lane and compares artifact hash.
