from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORTS_ROOT = REPO_ROOT / "docs" / "reports"
OUTPUTS_ROOT = REPO_ROOT / "outputs"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def _render_summary(phase_name: str, payload: dict, runner: str, assertion: str, output_name: str) -> str:
    checks = [key for key, value in payload.items() if isinstance(value, bool)]
    passed = sum(1 for key in checks if payload[key] is True)
    source_hash = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"""# {phase_name} Executive Summary

- Source report digest: `{source_hash[:20]}...`
- Gate result: **{'PASS' if payload.get('overall_pass') else 'FAIL'}**
- Source artifact: `outputs/{output_name}`
- Gate runner: `{runner}`
- Assertion runner: `{assertion}`
- Boolean checks passing: **{passed}/{len(checks)}**

## Key Signals
```json
{json.dumps({k: v for k, v in payload.items() if isinstance(v, bool)}, indent=2, sort_keys=True)}
```
"""


def _render_results(phase_name: str, payload: dict) -> str:
    checks = {k: v for k, v in payload.items() if isinstance(v, bool)}
    failed = [key for key, value in checks.items() if not value]
    return f"""# {phase_name} Test Results

- Overall pass: `{payload.get('overall_pass')}`
- Total boolean checks: `{len(checks)}`
- Failed checks: `{len(failed)}`

## Failed Checks
{('- none' if not failed else '\n'.join(f'- `{item}`' for item in failed))}

## Raw Report
```json
{json.dumps(payload, indent=2, sort_keys=True)}
```
"""


def main() -> int:
    phase3a = _load(OUTPUTS_ROOT / "phase3a_gate_report.json")
    phase3b = _load(OUTPUTS_ROOT / "phase3b_gate_report.json")

    _write(
        REPORTS_ROOT / "phase3a" / "executive_summary.md",
        _render_summary(
            "Phase 3A",
            phase3a,
            "scripts/run_phase3a_gate.sh",
            "scripts/assert_phase3a_gate_report.py",
            "phase3a_gate_report.json",
        ),
    )
    _write(
        REPORTS_ROOT / "phase3a" / "test_results.md",
        _render_results("Phase 3A", phase3a),
    )

    _write(
        REPORTS_ROOT / "phase3b" / "executive_summary.md",
        _render_summary(
            "Phase 3B",
            phase3b,
            "scripts/run_phase3b_gate.sh",
            "scripts/assert_phase3b_gate_report.py",
            "phase3b_gate_report.json",
        ),
    )
    _write(
        REPORTS_ROOT / "phase3b" / "test_results.md",
        _render_results("Phase 3B", phase3b),
    )

    print("phase3 report pack refreshed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
