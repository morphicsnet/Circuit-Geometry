use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Error, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum GeoCltError {
    #[error("validation error: {0}")]
    Validation(String),
    #[error("serialization error: {0}")]
    Serialization(String),
    #[error("not found: {0}")]
    NotFound(String),
    #[error("unsupported: {0}")]
    Unsupported(String),
    #[error("internal error: {0}")]
    Internal(String),
}

#[cfg(test)]
mod tests {
    use super::GeoCltError;

    #[test]
    fn error_variants_roundtrip_through_json() {
        let error = GeoCltError::Validation("bad payload".to_string());
        let encoded = serde_json::to_string(&error).expect("encode");
        let decoded: GeoCltError = serde_json::from_str(&encoded).expect("decode");
        assert_eq!(decoded, error);
    }
}
