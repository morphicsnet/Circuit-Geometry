//! Shared typed units used throughout Geo-CLT records and kernels.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub struct LayerIndex(pub u32);

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub struct TokenIndex(pub i32);

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct Score(pub f64);

#[cfg(test)]
mod tests {
    use super::{LayerIndex, Score, TokenIndex};

    #[test]
    fn units_roundtrip_through_json() {
        let layer: LayerIndex = serde_json::from_str(&serde_json::to_string(&LayerIndex(7)).expect("encode layer"))
            .expect("decode layer");
        let token: TokenIndex =
            serde_json::from_str(&serde_json::to_string(&TokenIndex(-2)).expect("encode token"))
                .expect("decode token");
        let score: Score = serde_json::from_str(&serde_json::to_string(&Score(0.42)).expect("encode score"))
            .expect("decode score");

        assert_eq!(layer, LayerIndex(7));
        assert_eq!(token, TokenIndex(-2));
        assert_eq!(score, Score(0.42));
    }
}
