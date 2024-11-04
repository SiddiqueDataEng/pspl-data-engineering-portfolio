#!/usr/bin/env bash
# Run Airflow standalone inside WSL (POSIX). Invoked by scripts/run-airflow-wsl.ps1.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

VENV="${REPO_ROOT}/.venv-wsl"
PY="${VENV}/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "Creating WSL virtualenv at .venv-wsl ..."
  if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found in WSL. Install: sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
    exit 1
  fi
  python3 -m venv "$VENV"
  "$PY" -m pip install --upgrade pip
  MINOR="$("$PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  CONSTRAINT="https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-${MINOR}.txt"
  echo "Installing apache-airflow==2.10.4 (constraints for Python ${MINOR}) ..."
  "$PY" -m pip install "apache-airflow==2.10.4" --constraint "$CONSTRAINT"
  "$PY" -m pip install "typing_extensions>=4.14.1" "psutil>=7" pendulum duckdb \
    "dbt-core==1.8.4" "dbt-duckdb==1.8.1"
fi

export AIRFLOW_HOME="${REPO_ROOT}/airflow/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="${REPO_ROOT}/airflow/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__LOGGING__CREATE_LATEST_LOG_LINK=False
export PORTFOLIO_REPO_ROOT="${REPO_ROOT}"
export DELTA_LAKE_PATH="${REPO_ROOT}/delta_lake"

# Reachable from Windows browser via localhost (WSL2 forwards ports).
export AIRFLOW__WEBSERVER__WEB_SERVER_HOST=0.0.0.0
export AIRFLOW__WEBSERVER__WEB_SERVER_PORT=8080

mkdir -p "$AIRFLOW_HOME"

echo "AIRFLOW_HOME=${AIRFLOW_HOME}"
echo "UI: http://localhost:8080 (from Windows host)"
echo "Starting airflow standalone (Ctrl+C to stop) ..."
exec "${VENV}/bin/airflow" standalone
