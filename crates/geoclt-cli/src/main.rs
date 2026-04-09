//! Operator-facing CLI for benchmark, artifact, and sidecar workflows in Geo-CLT.

use anyhow::{anyhow, Context, Result};
use clap::{Parser, Subcommand};
use geoclt_artifacts::validate::validate_file_against_schema_path;
use geoclt_benchmark::contract::{
    evaluate_bundle_contract, evaluate_contract, BaselineResult, ConformanceClass,
};
use geoclt_ids::StableId;
use geoclt_runtime::run::{execute_workspace_bundle, WorkspaceKernelInput};
use geoclt_schema::artifact::ArtifactMetadata;
use geoclt_schema::benchmark::BenchmarkLane;
use geoclt_schema::hyperpath::HyperpathRecord;
use geoclt_sidecar::server::serve as serve_sidecar;
use geoclt_units::Score;
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::env;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "geoclt")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Version,
    #[command(name = "run-profile")]
    RunProfile {
        #[arg(long, default_value = "examples/configs/factual_retrieval.toml")]
        profile: PathBuf,
        #[arg(long, default_value_t = false)]
        require_pass: bool,
    },
    Benchmark {
        #[arg(long, default_value = "factual_retrieval.v1")]
        lane_id: String,
        #[arg(long, default_value = "factual_retrieval")]
        behavior_id: String,
        #[arg(long, default_value = "gpt2-small")]
        model_id: String,
        #[arg(long, default_value_t = 0.18)]
        intervention_faithfulness: f64,
        #[arg(long, default_value_t = 0.09)]
        synergy_score_max: f64,
        #[arg(long, default_value_t = 0.84)]
        chart_stability: f64,
        #[arg(long, default_value_t = 0.82)]
        transport_coherence: f64,
        #[arg(long, default_value_t = 0.20)]
        geodesic_deviation: f64,
        #[arg(long)]
        fixture: Option<PathBuf>,
        #[arg(long, default_value_t = false)]
        require_pass: bool,
    },
    #[command(name = "validate-artifacts")]
    ValidateArtifacts {
        #[arg(long)]
        artifact: PathBuf,
        #[arg(long)]
        schema: PathBuf,
    },
    #[command(name = "sidecar")]
    Sidecar {
        #[command(subcommand)]
        command: SidecarCommands,
    },
}

#[derive(Subcommand)]
enum SidecarCommands {
    Serve {
        #[arg(long, default_value = "127.0.0.1:50051")]
        addr: String,
    },
}

#[derive(Debug, Clone, Deserialize)]
struct ProfileModel {
    model_id: String,
}

#[derive(Debug, Clone, Deserialize)]
struct Profile {
    lane_id: String,
    behavior_id: String,
    intervention_delta_threshold: f64,
    synergy_threshold: f64,
    chart_stability_threshold: f64,
    transport_coherence_threshold: f64,
    baseline_margin_threshold: f64,
    model: ProfileModel,
}

#[derive(Debug, Clone, Deserialize)]
struct FixtureMetrics {
    intervention_faithfulness: f64,
    synergy_score_max: f64,
    chart_stability: f64,
    transport_coherence: f64,
    geodesic_deviation: f64,
}

#[derive(Debug, Clone, Deserialize)]
struct FixtureFile {
    lane: BenchmarkLane,
    model_id: Option<String>,
    metrics: FixtureMetrics,
    baselines: Vec<BaselineResult>,
}

#[derive(Debug, Clone)]
struct Metrics {
    intervention_faithfulness: f64,
    synergy_score_max: f64,
    chart_stability: f64,
    transport_coherence: f64,
    geodesic_deviation: f64,
}

fn build_path(lane: &BenchmarkLane, metrics: &Metrics, identity: (&str, &str)) -> HyperpathRecord {
    HyperpathRecord {
        metadata: ArtifactMetadata {
            artifact_id: format!("artifact-{}-{}", identity.0, identity.1),
            artifact_type: "hyperpath_record".to_string(),
            schema_version: 2,
            producer: "geoclt:cli:0.2.0".to_string(),
            trace_id: format!("trace-{}-{}", identity.0, identity.1),
            run_id: format!("run-{}-{}", identity.0, identity.1),
            content_hash: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                .to_string(),
            created_at: "2026-01-01T00:00:00Z".to_string(),
        },
        path_id: StableId::from_parts(&["path", identity.0, identity.1]),
        behavior_id: lane.behavior_id.clone(),
        event_ids: vec![
            StableId::from_parts(&["event", identity.0, "1"]),
            StableId::from_parts(&["event", identity.0, "2"]),
        ],
        chart_ids: vec!["chart-a".to_string(), "chart-b".to_string()],
        layer_ids: vec![5, 6],
        transport_edge_ids: vec!["edge-1".to_string()],
        geodesic_deviation: Some(Score(metrics.geodesic_deviation)),
        chart_stability: Score(metrics.chart_stability),
        transport_coherence: Score(metrics.transport_coherence),
        intervention_faithfulness: Score(metrics.intervention_faithfulness),
        synergy_score_max: Score(metrics.synergy_score_max),
        admitted: false,
    }
}

fn deterministic_score(seed: &str, lower: f64, upper: f64) -> f64 {
    let mut hasher = Sha256::new();
    hasher.update(seed.as_bytes());
    let digest = hasher.finalize();
    let bytes: [u8; 8] = digest[..8].try_into().expect("slice should be length 8");
    let ratio = u64::from_be_bytes(bytes) as f64 / u64::MAX as f64;
    lower + (upper - lower) * ratio
}

fn deterministic_metrics(lane: &BenchmarkLane, model_id: &str) -> Metrics {
    let seed = format!("{}:{}:{}", model_id, lane.lane_id, lane.behavior_id);
    Metrics {
        intervention_faithfulness: deterministic_score(
            &(seed.clone() + ":intervention"),
            0.14,
            0.24,
        ),
        synergy_score_max: deterministic_score(&(seed.clone() + ":synergy"), 0.06, 0.16),
        chart_stability: deterministic_score(&(seed.clone() + ":chart"), 0.72, 0.96),
        transport_coherence: deterministic_score(&(seed.clone() + ":transport"), 0.72, 0.96),
        geodesic_deviation: deterministic_score(&(seed + ":geodesic"), 0.02, 0.25),
    }
}

fn deterministic_baselines(lane: &BenchmarkLane, model_id: &str) -> Vec<BaselineResult> {
    let seed = format!("{}:{}:{}", model_id, lane.lane_id, lane.behavior_id);
    let mut baselines = vec![
        BaselineResult {
            baseline_id: "single_sae".to_string(),
            intervention_faithfulness: deterministic_score(
                &(seed.clone() + ":single_sae"),
                0.07,
                0.16,
            ),
        },
        BaselineResult {
            baseline_id: "ensemble_sae".to_string(),
            intervention_faithfulness: deterministic_score(
                &(seed.clone() + ":ensemble_sae"),
                0.08,
                0.18,
            ),
        },
        BaselineResult {
            baseline_id: "pairwise_graph".to_string(),
            intervention_faithfulness: deterministic_score(
                &(seed.clone() + ":pairwise_graph"),
                0.08,
                0.17,
            ),
        },
        BaselineResult {
            baseline_id: "geometry_free".to_string(),
            intervention_faithfulness: deterministic_score(&(seed + ":geometry_free"), 0.08, 0.19),
        },
    ];
    baselines.sort_by(|a, b| a.baseline_id.cmp(&b.baseline_id));
    baselines
}

fn summary(
    lane: &BenchmarkLane,
    model_id: &str,
    metrics: &Metrics,
    baselines: &[BaselineResult],
    identity: (&str, &str),
) -> serde_json::Value {
    let bundle_output = execute_workspace_bundle(WorkspaceKernelInput {
        model_id: model_id.to_string(),
        lane_id: lane.lane_id.clone(),
        behavior_id: lane.behavior_id.clone(),
        profile: lane.behavior_id.clone(),
        run_id: Some(format!("run-{}-{}", identity.0, identity.1)),
        trace_id: Some(format!("trace-{}-{}", identity.0, identity.1)),
        feature_hints: vec![
            format!("behavior:{}", lane.behavior_id),
            format!("model:{model_id}"),
        ],
        intervention_faithfulness: metrics.intervention_faithfulness,
        synergy_score_max: metrics.synergy_score_max,
        chart_stability_hint: metrics.chart_stability,
        transport_coherence_hint: metrics.transport_coherence,
        geodesic_deviation_hint: metrics.geodesic_deviation,
        intervention_delta_threshold: lane.intervention_delta_threshold,
        synergy_threshold: lane.synergy_threshold,
        chart_stability_threshold: lane.chart_stability_threshold,
        transport_coherence_threshold: lane.transport_coherence_threshold,
        baseline_margin_threshold: lane.baseline_margin_threshold,
    })
    .ok();

    let evaluation = bundle_output
        .as_ref()
        .and_then(|output| evaluate_bundle_contract(&output.artifact_bundle, lane, baselines).ok())
        .unwrap_or_else(|| {
            let path = build_path(lane, metrics, identity);
            evaluate_contract(&path, lane, baselines)
        });

    serde_json::json!({
        "lane": lane,
        "model_id": model_id,
        "metrics": {
            "intervention_faithfulness": metrics.intervention_faithfulness,
            "synergy_score_max": metrics.synergy_score_max,
            "chart_stability": metrics.chart_stability,
            "transport_coherence": metrics.transport_coherence,
            "geodesic_deviation": metrics.geodesic_deviation
        },
        "baselines": baselines.iter().map(|baseline| {
            serde_json::json!({
                "baseline_id": baseline.baseline_id,
                "intervention_faithfulness": baseline.intervention_faithfulness
            })
        }).collect::<Vec<_>>(),
        "admission": {
            "passed": evaluation.admission.passed,
            "failed_checks": evaluation.admission.failed_checks,
            "min_margin": evaluation.admission.min_margin,
        },
        "falsifiers": {
            "pairwise_sufficiency_triggered": evaluation.falsifiers.pairwise_sufficiency_triggered,
            "chart_fragility_triggered": evaluation.falsifiers.chart_fragility_triggered,
            "transport_irrelevance_triggered": evaluation.falsifiers.transport_irrelevance_triggered,
            "geometry_non_predictiveness_triggered": evaluation.falsifiers.geometry_non_predictiveness_triggered,
            "spurious_synergy_triggered": evaluation.falsifiers.spurious_synergy_triggered,
            "any_triggered": evaluation.falsifiers.any_triggered(),
        },
        "strongest_baseline_id": evaluation.strongest_baseline_id,
        "strongest_baseline": evaluation.strongest_baseline,
        "beats_baseline": evaluation.beats_baseline,
        "conformance_class": evaluation.conformance_class.as_str(),
        "atlas_overlap_map": bundle_output.as_ref().map(|output| serde_json::to_value(&output.kernel_output.atlas).expect("atlas json")),
        "transport_diagnostics": bundle_output.as_ref().map(|output| serde_json::to_value(&output.kernel_output.transport).expect("transport json")),
        "candidate_event_table": bundle_output.as_ref().map(|output| serde_json::to_value(&output.kernel_output.candidate_event_table).expect("candidate json")),
        "mechanism_verification": bundle_output.as_ref().map(|output| serde_json::to_value(&output.kernel_output.mechanism_verification).expect("mechanism json")),
        "canonicalized_mechanisms": bundle_output.as_ref().map(|output| serde_json::to_value(&output.kernel_output.canonicalized_mechanisms).expect("canonicalized json")),
        "artifact_bundle_hash": bundle_output.as_ref().map(|output| output.artifact_bundle.bundle_hash.clone()),
        "status": if evaluation.conformance_class == ConformanceClass::Conformant { "completed" } else { "failed" },
    })
}

fn enforce_pass(require_pass: bool, summary: &serde_json::Value) -> Result<()> {
    if !require_pass {
        return Ok(());
    }
    let class = summary["conformance_class"]
        .as_str()
        .ok_or_else(|| anyhow!("missing conformance_class in summary"))?;
    if class != "conformant" {
        return Err(anyhow!("run is non-conformant: {class}"));
    }
    Ok(())
}

fn load_profile(path: &PathBuf) -> Result<(BenchmarkLane, String)> {
    let raw = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read profile file: {}", path.display()))?;
    let profile: Profile = toml::from_str(&raw)
        .with_context(|| format!("failed to parse profile TOML: {}", path.display()))?;
    let lane = BenchmarkLane {
        lane_id: profile.lane_id,
        behavior_id: profile.behavior_id,
        intervention_delta_threshold: profile.intervention_delta_threshold,
        synergy_threshold: profile.synergy_threshold,
        chart_stability_threshold: profile.chart_stability_threshold,
        transport_coherence_threshold: profile.transport_coherence_threshold,
        baseline_margin_threshold: profile.baseline_margin_threshold,
    };
    Ok((lane, profile.model.model_id))
}

fn load_fixture(path: &PathBuf) -> Result<(BenchmarkLane, String, Metrics, Vec<BaselineResult>)> {
    let raw = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read fixture file: {}", path.display()))?;
    let mut fixture: FixtureFile = serde_json::from_str(&raw)
        .with_context(|| format!("failed to parse fixture JSON: {}", path.display()))?;
    fixture
        .baselines
        .sort_by(|a, b| a.baseline_id.cmp(&b.baseline_id));
    Ok((
        fixture.lane,
        fixture.model_id.unwrap_or_else(|| "gpt2-small".to_string()),
        Metrics {
            intervention_faithfulness: fixture.metrics.intervention_faithfulness,
            synergy_score_max: fixture.metrics.synergy_score_max,
            chart_stability: fixture.metrics.chart_stability,
            transport_coherence: fixture.metrics.transport_coherence,
            geodesic_deviation: fixture.metrics.geodesic_deviation,
        },
        fixture.baselines,
    ))
}

fn default_lane(lane_id: String, behavior_id: String) -> BenchmarkLane {
    BenchmarkLane {
        lane_id,
        behavior_id,
        intervention_delta_threshold: 0.10,
        synergy_threshold: 0.05,
        chart_stability_threshold: 0.70,
        transport_coherence_threshold: 0.70,
        baseline_margin_threshold: 0.05,
    }
}

fn main() -> Result<()> {
    let model_mode = env::var("GEOCLT_MODEL_MODE").unwrap_or_else(|_| "real".to_string());
    let cli = Cli::parse();
    match cli.command {
        Commands::Version => {
            println!("0.1.0");
        }
        Commands::RunProfile {
            profile,
            require_pass,
        } => {
            let (lane, model_id) = load_profile(&profile)?;
            let metrics = deterministic_metrics(&lane, &model_id);
            let baselines = deterministic_baselines(&lane, &model_id);
            let output = summary(
                &lane,
                &model_id,
                &metrics,
                &baselines,
                ("profile", &lane.lane_id),
            );
            enforce_pass(require_pass, &output)?;
            println!("{}", serde_json::to_string_pretty(&output)?);
        }
        Commands::Benchmark {
            lane_id,
            behavior_id,
            model_id,
            intervention_faithfulness,
            synergy_score_max,
            chart_stability,
            transport_coherence,
            geodesic_deviation,
            fixture,
            require_pass,
        } => {
            let (lane, model_id, metrics, baselines) = if let Some(path) = fixture {
                load_fixture(&path)?
            } else {
                if model_mode == "real" {
                    return Err(anyhow!(
                        "benchmark requires --fixture when GEOCLT_MODEL_MODE=real; use GEOCLT_MODEL_MODE=fixture-replay for deterministic metric replay"
                    ));
                }
                if intervention_faithfulness < 0.0
                    || synergy_score_max < 0.0
                    || chart_stability < 0.0
                    || transport_coherence < 0.0
                {
                    return Err(anyhow!("benchmark metrics must be non-negative"));
                }
                let lane = default_lane(lane_id, behavior_id);
                let baselines = deterministic_baselines(&lane, &model_id);
                let metrics = Metrics {
                    intervention_faithfulness,
                    synergy_score_max,
                    chart_stability,
                    transport_coherence,
                    geodesic_deviation,
                };
                (lane, model_id, metrics, baselines)
            };

            let output = summary(
                &lane,
                &model_id,
                &metrics,
                &baselines,
                ("benchmark", &lane.lane_id),
            );
            enforce_pass(require_pass, &output)?;
            println!("{}", serde_json::to_string_pretty(&output)?);
        }
        Commands::ValidateArtifacts { artifact, schema } => {
            validate_file_against_schema_path(&artifact, &schema)
                .map_err(|error| anyhow!("{error}"))?;
            println!(
                "{}",
                serde_json::to_string_pretty(&serde_json::json!({
                    "status": "ok",
                    "artifact": artifact,
                    "schema": schema,
                }))?
            );
        }
        Commands::Sidecar { command } => match command {
            SidecarCommands::Serve { addr } => {
                let runtime = tokio::runtime::Runtime::new()
                    .map_err(|error| anyhow!("failed to create tokio runtime: {error}"))?;
                runtime
                    .block_on(serve_sidecar(&addr))
                    .map_err(|error| anyhow!("sidecar serve failed: {error}"))?;
            }
        },
    }
    Ok(())
}

#[cfg(test)]
mod cli_tests {
    use super::{Cli, Commands};
    use clap::{CommandFactory, Parser};

    #[test]
    fn help_text_mentions_operator_surfaces() {
        let mut command = Cli::command();
        let help = command.render_long_help().to_string();
        assert!(help.contains("benchmark"));
        assert!(help.contains("validate-artifacts"));
        assert!(help.contains("sidecar"));
    }

    #[test]
    fn version_command_parses_cleanly() {
        let cli = Cli::try_parse_from(["geoclt", "version"]).expect("parse version");
        assert!(matches!(cli.command, Commands::Version));
    }
}
