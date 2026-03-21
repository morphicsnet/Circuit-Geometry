from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_ROOT = REPO_ROOT / "outputs"
REPORTS_ROOT = REPO_ROOT / "docs" / "reports"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def _render_results(title: str, payload: dict) -> str:
    checks = {k: v for k, v in payload.items() if isinstance(v, bool)}
    failed = [k for k, v in checks.items() if not v]
    failed_body = "- none" if not failed else "\n".join(f"- `{item}`" for item in failed)
    return f"""# {title} Test Results

- Overall pass: `{payload.get('overall_pass')}`
- Total boolean checks: `{len(checks)}`
- Failed checks: `{len(failed)}`

## Failed Checks
{failed_body}

## Raw Report
```json
{json.dumps(payload, indent=2, sort_keys=True)}
```
"""


def _render_phase4a_summary(gate: dict, nightly: dict | None) -> str:
    gate_checks = [k for k, v in gate.items() if isinstance(v, bool)]
    gate_passed = sum(1 for key in gate_checks if gate[key] is True)
    nightly_status = "MISSING"
    nightly_passed = 0
    nightly_total = 0
    if nightly is not None:
        nightly_checks = [k for k, v in nightly.items() if isinstance(v, bool)]
        nightly_total = len(nightly_checks)
        nightly_passed = sum(1 for key in nightly_checks if nightly[key] is True)
        nightly_status = "PASS" if nightly.get("overall_pass") else "FAIL"

    return f"""# Phase 4A Executive Summary

- Gate result: **{'PASS' if gate.get('overall_pass') else 'FAIL'}**
- Source artifact (CI): `outputs/phase4a_gate_report.json`
- Source artifact (nightly real-model): `outputs/phase4a_nightly_model_report.json`
- CI gate status: **{'PASS' if gate.get('overall_pass') else 'FAIL'}**
- Nightly real-model validation status: **{nightly_status}**
- CI checks passing: **{gate_passed}/{len(gate_checks)}**
- Nightly checks passing: **{nightly_passed}/{nightly_total}**

## CI Booleans
```json
{json.dumps({k: v for k, v in gate.items() if isinstance(v, bool)}, indent=2, sort_keys=True)}
```

## Nightly Booleans
```json
{json.dumps({k: v for k, v in (nightly or {}).items() if isinstance(v, bool)}, indent=2, sort_keys=True)}
```
"""


def _render_phase4b_summary(gate: dict) -> str:
    checks = [k for k, v in gate.items() if isinstance(v, bool)]
    passed = sum(1 for key in checks if gate[key] is True)
    return f"""# Phase 4B Executive Summary

- Gate result: **{'PASS' if gate.get('overall_pass') else 'FAIL'}**
- Source artifact: `outputs/phase4b_gate_report.json`
- Boolean checks passing: **{passed}/{len(checks)}**

## Key Booleans
```json
{json.dumps({k: v for k, v in gate.items() if isinstance(v, bool)}, indent=2, sort_keys=True)}
```
"""


def _refresh_phase4a() -> None:
    gate = _load(OUTPUTS_ROOT / "phase4a_gate_report.json")
    nightly_path = OUTPUTS_ROOT / "phase4a_nightly_model_report.json"
    nightly = _load(nightly_path) if nightly_path.exists() else None

    phase_dir = REPORTS_ROOT / "phase4a"
    _write(phase_dir / "executive_summary.md", _render_phase4a_summary(gate, nightly))
    _write(phase_dir / "test_results.md", _render_results("Phase 4A", gate))


def _refresh_phase4b() -> None:
    gate = _load(OUTPUTS_ROOT / "phase4b_gate_report.json")
    phase_dir = REPORTS_ROOT / "phase4b"
    _write(phase_dir / "executive_summary.md", _render_phase4b_summary(gate))
    _write(phase_dir / "test_results.md", _render_results("Phase 4B", gate))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["phase4a", "phase4b", "all"], default="all")
    args = parser.parse_args()

    if args.phase in {"phase4a", "all"}:
        _refresh_phase4a()
    if args.phase in {"phase4b", "all"}:
        _refresh_phase4b()

    print(f"phase4 report pack refreshed ({args.phase})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
