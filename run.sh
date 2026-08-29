#!/usr/bin/env bash
# Aksara launcher for Linux and macOS.
# It deliberately tests runnable interpreters instead of assuming a `python`
# PATH alias exists. This avoids false "Python not found" errors on systems
# that expose Python only as python3.

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

supports_aksara_python() {
    "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
        >/dev/null 2>&1
}

for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && supports_aksara_python "$candidate"; then
        exec "$candidate" "$ROOT/run.py" "$@"
    fi
done

# A previously created project venv remains a valid fallback if PATH changes.
if [[ -x "$ROOT/.venv/bin/python" ]] && supports_aksara_python "$ROOT/.venv/bin/python"; then
    exec "$ROOT/.venv/bin/python" "$ROOT/run.py" "$@"
fi

echo "Aksara needs a runnable Python 3.10+ interpreter." >&2
echo "Tried python3, python, and .venv/bin/python. Install Python from https://python.org/downloads" >&2
exit 1
