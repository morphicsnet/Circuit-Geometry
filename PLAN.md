# Geo-CLT-SAE local checklist

Source of truth: [`/Volumes/128/MAIR/PLAN.md`](/Volumes/128/MAIR/PLAN.md)

## Geo-owned surfaces
- `python/geoclt/mair_runtime.py`
- `python/geoclt/workspace.py`
- `python/tests/test_mair_benchmark.py`

## Current blockers
- remove MAIR path hacks from the receipt lane
- keep `Workspace.run_mair_benchmark(...)` stable while the upstream capture backend changes

## Upstream dependency
- `MAIR`, `BLT`, and `hypercircuit` must be installed or importable before the MAIR benchmark integration test runs
