#[derive(Debug, Clone, Copy)]
pub struct Backpressure {
    pub queue_depth: usize,
    pub recommended_delay_ms: u32,
}

pub fn backpressure_signal(queue_depth: usize) -> Backpressure {
    let recommended_delay_ms = if queue_depth > 200 {
        200
    } else if queue_depth > 100 {
        100
    } else if queue_depth > 50 {
        50
    } else {
        0
    };

    Backpressure {
        queue_depth,
        recommended_delay_ms,
    }
}
