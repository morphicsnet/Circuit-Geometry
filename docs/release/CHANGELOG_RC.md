# Internal RC Changelog

## v0.1.0-rc1

### Added
- release readiness orchestration (`scripts/run_release_candidate.sh`)
- release readiness report generation and assertions
- synthetic inventory report generation
- release evidence packaging manifest
- release baseline freeze and RC runbook docs

### Changed
- release workflow now executes full real gate pipeline
- wheel workflow hardening with build matrix and smoke checks
- placeholder guard expanded to production runtime paths

### Notes
- PR stub gate and nightly real-model validation remain separately reported.
