use std::collections::BTreeMap;
use std::env;
use std::sync::Arc;

use geoclt_artifacts::bundle::validate_artifact_bundle;
use geoclt_artifacts::registry::{load_packaged_registry, SchemaRegistry};
use geoclt_schema::artifact::ArtifactBundle;
use tokio::sync::Mutex;
use tonic::{Request, Response, Status};

use crate::batching::{backpressure_signal, Backpressure};
use crate::emit::assemble_bundle;
use crate::proto::sidecar_service_server::{SidecarService, SidecarServiceServer};
use crate::proto::{
    Ack, ActivationChunk, ArtifactInline, ServerStatus, TraceAbort, TraceEnd, TraceStart,
};
use crate::trace_state::{TraceContext, TraceStage};

#[derive(Debug, Clone)]
pub struct SidecarServer {
    producer: String,
    registry: SchemaRegistry,
    traces: BTreeMap<String, TraceContext>,
}

impl SidecarServer {
    pub fn new(producer: &str, registry: SchemaRegistry) -> Self {
        Self {
            producer: producer.to_string(),
            registry,
            traces: BTreeMap::new(),
        }
    }

    pub fn start_trace(
        &mut self,
        trace_id: &str,
        adapter_id: &str,
        model_id: &str,
        lane_id: &str,
        run_id: &str,
        started_at: &str,
    ) -> Result<(), String> {
        let context = TraceContext::new(
            trace_id.to_string(),
            adapter_id.to_string(),
            model_id.to_string(),
            lane_id.to_string(),
            run_id.to_string(),
            started_at.to_string(),
        );
        self.traces.insert(trace_id.to_string(), context);
        Ok(())
    }

    pub fn push_chunk(
        &mut self,
        trace_id: &str,
        chunk_idempotency_key: &str,
        payload: Vec<u8>,
    ) -> Result<(Backpressure, bool), String> {
        let context = self
            .traces
            .get_mut(trace_id)
            .ok_or_else(|| format!("trace not found: {trace_id}"))?;

        if let Some(existing) = context.chunks.get(chunk_idempotency_key) {
            if existing == &payload {
                return Ok((backpressure_signal(context.chunks.len()), true));
            }
            context.stage = TraceStage::Failed;
            context.status = "FAILED".to_string();
            return Err("duplicate chunk conflict".to_string());
        }

        context.chunks.insert(chunk_idempotency_key.to_string(), payload);
        context.chunk_count = context.chunks.len();
        context.stage = TraceStage::Streaming;
        context.status = "STREAMING".to_string();
        Ok((backpressure_signal(context.chunk_count), false))
    }

    pub fn end_trace(&mut self, trace_id: &str) -> Result<ArtifactBundle, String> {
        let context = self
            .traces
            .get_mut(trace_id)
            .ok_or_else(|| format!("trace not found: {trace_id}"))?;
        if context.stage == TraceStage::Failed {
            return Err("trace is failed".to_string());
        }
        context.stage = TraceStage::Ended;
        context.status = "ENDED".to_string();

        let bundle = assemble_bundle(context, &self.producer)?;
        validate_artifact_bundle(&self.registry, &bundle)?;

        context.stage = TraceStage::Finalized;
        context.status = "FINALIZED".to_string();
        Ok(bundle)
    }

    pub fn abort_trace(&mut self, trace_id: &str) -> Result<(), String> {
        let context = self
            .traces
            .get_mut(trace_id)
            .ok_or_else(|| format!("trace not found: {trace_id}"))?;
        context.stage = TraceStage::Aborted;
        context.status = "ABORTED".to_string();
        Ok(())
    }

pub fn active_traces(&self) -> usize {
        self.traces
            .values()
            .filter(|trace| matches!(trace.stage, TraceStage::Started | TraceStage::Streaming))
            .count()
    }
}

#[derive(Clone)]
pub struct SidecarGrpcService {
    inner: Arc<Mutex<SidecarServer>>,
}

impl SidecarGrpcService {
    pub fn new(server: SidecarServer) -> Self {
        Self {
            inner: Arc::new(Mutex::new(server)),
        }
    }

    fn enforce_auth<T>(&self, request: &Request<T>) -> Result<(), Status> {
        let mode = env::var("GEOCLT_AUTH_MODE").unwrap_or_else(|_| "token".to_string());
        if mode != "token" {
            return Ok(());
        }
        let expected = env::var("GEOCLT_AUTH_TOKEN")
            .unwrap_or_else(|_| "geoclt-local-token".to_string());
        let metadata = request.metadata();
        let Some(value) = metadata.get("authorization") else {
            return Err(Status::unauthenticated("missing authorization token"));
        };
        let header = value
            .to_str()
            .map_err(|_| Status::unauthenticated("invalid authorization header"))?;
        if header != format!("Bearer {expected}") {
            return Err(Status::unauthenticated("invalid authorization token"));
        }
        Ok(())
    }
}

#[tonic::async_trait]
impl SidecarService for SidecarGrpcService {
    async fn start_trace(&self, request: Request<TraceStart>) -> Result<Response<Ack>, Status> {
        self.enforce_auth(&request)?;
        let req = request.into_inner();
        let mut guard = self.inner.lock().await;
        guard
            .start_trace(
                &req.trace_id,
                &req.adapter_id,
                &req.model_id,
                &req.lane_id,
                &req.run_id,
                &req.started_at,
            )
            .map_err(Status::internal)?;
        Ok(Response::new(Ack {
            ok: true,
            message: "trace started".to_string(),
        }))
    }

    async fn push_activation(
        &self,
        request: Request<ActivationChunk>,
    ) -> Result<Response<Ack>, Status> {
        self.enforce_auth(&request)?;
        let req = request.into_inner();
        let mut guard = self.inner.lock().await;
        let (bp, duplicate) = guard
            .push_chunk(&req.trace_id, &req.chunk_idempotency_key, req.payload)
            .map_err(Status::internal)?;
        Ok(Response::new(Ack {
            ok: true,
            message: if duplicate {
                "duplicate-noop".to_string()
            } else {
                format!("chunk accepted; queue_depth={}; delay_ms={}", bp.queue_depth, bp.recommended_delay_ms)
            },
        }))
    }

    async fn end_trace(
        &self,
        request: Request<TraceEnd>,
    ) -> Result<Response<ArtifactInline>, Status> {
        self.enforce_auth(&request)?;
        let req = request.into_inner();
        let mut guard = self.inner.lock().await;
        let bundle = guard.end_trace(&req.trace_id).map_err(Status::internal)?;
        let bundle_json = serde_json::to_vec(&bundle).map_err(|error| {
            Status::internal(format!("failed to serialize artifact bundle: {error}"))
        })?;
        Ok(Response::new(ArtifactInline {
            bundle_id: bundle.bundle_id,
            bundle_json,
            bundle_hash: bundle.bundle_hash,
        }))
    }

    async fn abort_trace(&self, request: Request<TraceAbort>) -> Result<Response<Ack>, Status> {
        self.enforce_auth(&request)?;
        let req = request.into_inner();
        let mut guard = self.inner.lock().await;
        guard.abort_trace(&req.trace_id).map_err(Status::internal)?;
        Ok(Response::new(Ack {
            ok: true,
            message: format!("aborted: {}", req.reason),
        }))
    }

    async fn get_status(&self, request: Request<Ack>) -> Result<Response<ServerStatus>, Status> {
        self.enforce_auth(&request)?;
        let guard = self.inner.lock().await;
        Ok(Response::new(ServerStatus {
            status: "ok".to_string(),
            active_traces: guard.active_traces() as u32,
        }))
    }
}

pub async fn serve(addr: &str) -> Result<(), Box<dyn std::error::Error>> {
    let registry = load_packaged_registry()?;
    let service = SidecarGrpcService::new(SidecarServer::new("geoclt:sidecar:0.2.0", registry));
    tonic::transport::Server::builder()
        .add_service(SidecarServiceServer::new(service))
        .serve(addr.parse()?)
        .await?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::SidecarServer;
    use geoclt_artifacts::registry::load_packaged_registry;

    fn server() -> SidecarServer {
        let registry = load_packaged_registry().expect("registry");
        SidecarServer::new("geoclt:sidecar:0.2.0", registry)
    }

    #[test]
    fn supports_duplicate_noop_and_conflict_fail() {
        let mut sidecar = server();
        sidecar
            .start_trace(
                "trace-1",
                "transformers",
                "gpt2-small",
                "factual_retrieval.v1",
                "run-1",
                "2026-01-01T00:00:00Z",
            )
            .expect("start");

        sidecar
            .push_chunk("trace-1", "key-1", b"abc".to_vec())
            .expect("first push");
        sidecar
            .push_chunk("trace-1", "key-1", b"abc".to_vec())
            .expect("duplicate noop");

        let conflict = sidecar.push_chunk("trace-1", "key-1", b"def".to_vec());
        assert!(conflict.is_err());
    }

    #[test]
    fn ends_trace_into_valid_bundle() {
        let mut sidecar = server();
        sidecar
            .start_trace(
                "trace-2",
                "transformers",
                "gpt2-small",
                "factual_retrieval.v1",
                "run-2",
                "2026-01-01T00:00:00Z",
            )
            .expect("start");
        sidecar
            .push_chunk("trace-2", "key-1", b"abc".to_vec())
            .expect("push");
        let bundle = sidecar.end_trace("trace-2").expect("end trace");
        assert_eq!(bundle.trace_id, "trace-2");
        assert!(bundle.immutable);
    }
}

#[cfg(test)]
mod more_tests {
    use super::SidecarServer;
    use geoclt_artifacts::registry::load_packaged_registry;

    fn server() -> SidecarServer {
        let registry = load_packaged_registry().expect("registry");
        SidecarServer::new("geoclt:sidecar:0.2.0", registry)
    }

    #[test]
    fn concurrent_trace_separation() {
        let mut sidecar = server();
        sidecar
            .start_trace(
                "trace-a",
                "transformers",
                "gpt2-small",
                "factual_retrieval.v1",
                "run-a",
                "2026-01-01T00:00:00Z",
            )
            .expect("start a");
        sidecar
            .start_trace(
                "trace-b",
                "transformers",
                "gpt2-small",
                "factual_retrieval.v1",
                "run-b",
                "2026-01-01T00:00:00Z",
            )
            .expect("start b");

        sidecar
            .push_chunk("trace-a", "a-1", b"aaa".to_vec())
            .expect("chunk a");
        sidecar
            .push_chunk("trace-b", "b-1", b"bbb".to_vec())
            .expect("chunk b");

        let bundle_a = sidecar.end_trace("trace-a").expect("end a");
        let bundle_b = sidecar.end_trace("trace-b").expect("end b");

        assert_eq!(bundle_a.trace_id, "trace-a");
        assert_eq!(bundle_b.trace_id, "trace-b");
        assert_ne!(bundle_a.bundle_hash, bundle_b.bundle_hash);
    }
}
