#!/usr/bin/env bash
set -euo pipefail
cd services/ui
python3 -m http.server 4173
