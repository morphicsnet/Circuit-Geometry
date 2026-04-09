//! Shared deterministic helpers, traits, and error types used across Geo-CLT crates.

pub mod deterministic;
pub mod error;
pub mod traits;

pub use error::GeoCltError;
pub type GeoCltResult<T> = Result<T, GeoCltError>;
