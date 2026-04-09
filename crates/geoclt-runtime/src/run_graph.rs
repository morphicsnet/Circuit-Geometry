use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RunStage {
    Ingest,
    Atlas,
    Metric,
    Transport,
    Hypergraph,
    VerifyMechanisms,
    Canonicalize,
    Validate,
    AssembleBundle,
    Persist,
    Report,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunGraph {
    pub stages: Vec<RunStage>,
}

impl Default for RunGraph {
    fn default() -> Self {
        Self {
            stages: vec![
                RunStage::Ingest,
                RunStage::Atlas,
                RunStage::Metric,
                RunStage::Transport,
                RunStage::Hypergraph,
                RunStage::VerifyMechanisms,
                RunStage::Canonicalize,
                RunStage::Validate,
                RunStage::AssembleBundle,
                RunStage::Persist,
                RunStage::Report,
            ],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{RunGraph, RunStage};

    #[test]
    fn default_run_graph_has_expected_stage_order() {
        let graph = RunGraph::default();
        assert_eq!(graph.stages.first(), Some(&RunStage::Ingest));
        assert_eq!(graph.stages.last(), Some(&RunStage::Report));
    }

    #[test]
    fn run_graph_roundtrips_through_json() {
        let graph = RunGraph::default();
        let encoded = serde_json::to_string(&graph).expect("encode");
        let decoded: RunGraph = serde_json::from_str(&encoded).expect("decode");
        assert_eq!(decoded.stages, graph.stages);
    }
}
