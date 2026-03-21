#!/usr/bin/env bash
set -euo pipefail

bash scripts/run_release_candidate.sh

commit="$(git rev-parse --short HEAD)"
archive="outputs/geoclt-internal-rc-${commit}.tar.gz"
tar -czf "${archive}" \
  outputs/release_evidence \
  outputs/release_evidence_manifest.json \
  outputs/release_readiness_report.json \
  docs/reports/phase01 \
  docs/reports/phase2 \
  docs/reports/phase3a \
  docs/reports/phase3b \
  docs/reports/phase4a \
  docs/reports/phase4b \
  docs/release

if [[ -n "${GEOCLT_RC_TAG:-}" ]]; then
  git tag -a "${GEOCLT_RC_TAG}" -m "Geo-CLT internal RC ${GEOCLT_RC_TAG}"
fi

echo "release archive created: ${archive}"
