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
