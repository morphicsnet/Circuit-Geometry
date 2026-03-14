#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RunStage {
    Ingest,
    Normalize,
    Canonicalize,
    Validate,
    AssembleBundle,
    Persist,
    Report,
}

#[derive(Debug, Clone)]
pub struct RunGraph {
    pub stages: Vec<RunStage>,
}

impl Default for RunGraph {
    fn default() -> Self {
        Self {
            stages: vec![
                RunStage::Ingest,
                RunStage::Normalize,
                RunStage::Canonicalize,
                RunStage::Validate,
                RunStage::AssembleBundle,
                RunStage::Persist,
                RunStage::Report,
            ],
        }
    }
}
