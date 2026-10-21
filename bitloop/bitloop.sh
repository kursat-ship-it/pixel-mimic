#!/usr/bin/env bash
# bitloop launcher. Python is picked in this order: $BITLOOP_PY, <repo>/.venv, <repo>/venv, python3 on PATH.
# Spec/output paths are relative to where you call it (spec-internal asset paths resolve next to the spec).
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${BITLOOP_PY:-}"
for c in "$DIR/../.venv/bin/python" "$DIR/../venv/bin/python"; do
  [ -n "$PY" ] && break
  [ -x "$c" ] && PY="$c"
done
[ -n "$PY" ] || PY=python3
PYTHONPATH="$DIR${PYTHONPATH:+:$PYTHONPATH}" exec "$PY" -m bitloop "$@"
