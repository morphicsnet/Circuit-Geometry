use std::collections::BTreeMap;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TraceStage {
    Init,
    Started,
    Streaming,
    Ended,
    Validated,
    Persisted,
    Finalized,
    Aborted,
    Failed,
}

#[derive(Debug, Clone)]
pub struct TraceContext {
    pub trace_id: String,
    pub adapter_id: String,
    pub model_id: String,
    pub lane_id: String,
    pub run_id: String,
    pub started_at: String,
    pub stage: TraceStage,
    pub chunk_count: usize,
    pub status: String,
    pub chunks: BTreeMap<String, Vec<u8>>,
}

impl TraceContext {
    pub fn new(
        trace_id: String,
        adapter_id: String,
        model_id: String,
        lane_id: String,
        run_id: String,
        started_at: String,
    ) -> Self {
        Self {
            trace_id,
            adapter_id,
            model_id,
            lane_id,
            run_id,
            started_at,
            stage: TraceStage::Started,
            chunk_count: 0,
            status: "STARTED".to_string(),
            chunks: BTreeMap::new(),
        }
    }
}
