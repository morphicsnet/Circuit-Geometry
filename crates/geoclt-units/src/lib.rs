use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub struct LayerIndex(pub u32);

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub struct TokenIndex(pub i32);

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct Score(pub f64);
