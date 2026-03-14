# Phase 4A Logic Specifications

Gate formula:

`PASS = M AND L AND D AND R AND P`

Where:

- `M`: frozen model profile and deterministic replay inputs
- `L`: lane registry + scorecards + fallback semantics
- `D`: demo flow executes through bounded API contract
- `R`: receipts/report bundle emitted and valid
- `P`: latency/memory/success/fallback budgets within thresholds

Nightly formula:

`NIGHTLY_PASS = P1 AND P2 AND S AND B AND R`

Where:

- `P1`: primary profile valid
- `P2`: challenger profile valid
- `S`: shared lane exercised by both models
- `B`: receipt bundle + perf metrics recorded
- `R`: nightly report completeness and optional divergence bound
