#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/.venv/bin/python"
PIP="${ROOT}/.venv/bin/pip"
if [[ ! -x "$PY" ]]; then
  echo "Missing $PY — create .venv first (e.g. python -m venv .venv && pip install -r requirements.txt)." >&2
  exit 1
fi
VER="$("$PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
CONSTRAINT="https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-${VER}.txt"
echo "Installing apache-airflow==2.10.4 with constraints for Python ${VER}"
"$PIP" install "apache-airflow==2.10.4" --constraint "$CONSTRAINT"
"$PIP" install "typing_extensions>=4.14.1"
echo "Done. Start with: ./scripts/airflow-standalone.sh (or Docker: docker compose -f docker-compose.airflow.yml up)"
