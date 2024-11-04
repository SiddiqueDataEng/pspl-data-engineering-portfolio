#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
AIRFLOW_BIN="${ROOT}/.venv/bin/airflow"
if [[ ! -x "$AIRFLOW_BIN" ]]; then
  echo "Missing $AIRFLOW_BIN — run ./scripts/install-airflow.sh first." >&2
  exit 1
fi
export AIRFLOW_HOME="${ROOT}/airflow/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="${ROOT}/airflow/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES="False"
mkdir -p "$AIRFLOW_HOME"
echo "AIRFLOW_HOME=$AIRFLOW_HOME"
echo "DAGs: $AIRFLOW__CORE__DAGS_FOLDER"
echo "Starting Airflow standalone (Ctrl+C to stop)..."
exec "$AIRFLOW_BIN" standalone
