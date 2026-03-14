use geoclt_schema::artifact::ArtifactBundle;

use crate::batch::execute_batch;
use crate::run_graph::RunGraph;
use crate::stream::execute_stream;

pub fn execute_batch_graph(run_id: &str, trace_id: &str) -> Result<(RunGraph, ArtifactBundle), String> {
    let graph = RunGraph::default();
    let bundle = execute_batch(run_id, trace_id)?;
    Ok((graph, bundle))
}

pub fn execute_stream_graph(
    run_id: &str,
    trace_id: &str,
    chunks: &[Vec<u8>],
) -> Result<(RunGraph, ArtifactBundle), String> {
    let graph = RunGraph::default();
    let bundle = execute_stream(run_id, trace_id, chunks)?;
    Ok((graph, bundle))
}

#[cfg(test)]
mod tests {
    use super::{execute_batch_graph, execute_stream_graph};

    #[test]
    fn batch_and_stream_produce_stable_hash_for_identical_inputs() {
        let (_, first_batch) = execute_batch_graph("run-1", "trace-1").expect("batch one");
        let (_, second_batch) = execute_batch_graph("run-1", "trace-1").expect("batch two");
        assert_eq!(first_batch.bundle_hash, second_batch.bundle_hash);

        let chunks = vec![b"abc".to_vec(), b"def".to_vec()];
        let (_, first_stream) = execute_stream_graph("run-2", "trace-2", &chunks).expect("stream one");
        let (_, second_stream) = execute_stream_graph("run-2", "trace-2", &chunks).expect("stream two");
        assert_eq!(first_stream.bundle_hash, second_stream.bundle_hash);
    }
}
