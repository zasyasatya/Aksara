#!/usr/bin/env bash
# Install Aksara without Docker, then exit. All setup logic lives in run.py so
# installation and normal launches use the same Python/venv detection path.

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/run.sh" --install-only "$@"
