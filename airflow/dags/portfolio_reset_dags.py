"""
Airflow DAGs for scheduled or manual resets of generated artifacts.

Each DAG is ``schedule=None`` (trigger only). Pick the DAG that matches the layer
you want to wipe, then re-run the appropriate pipeline DAG or scripts.

Scopes mirror ``scripts/reset_project.py`` / ``scripts/reset-project.ps1``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator

REPO_ROOT = Path(__file__).resolve().parents[2]

_RESET_SCOPES = [
    "Full",
    "Datagenerator",
    "MedallionFull",
    "MedallionBronze",
    "MedallionSilver",
    "MedallionGold",
    "DbtSql",
    "Streamlit",
]


def _repo_root() -> Path:
    override = os.environ.get("PORTFOLIO_REPO_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return REPO_ROOT


def _make_reset_fn(scope: str, include_airflow_home: bool):
    def _run(**_context) -> None:
        repo = _repo_root()
        script = repo / "scripts" / "reset_project.py"
        if not script.is_file():
            raise AirflowException(f"Missing reset script: {script}")
        py = repo / ".venv" / "Scripts" / "python.exe" if sys.platform == "win32" else repo / ".venv" / "bin" / "python"
        exe = str(py) if py.is_file() else sys.executable
        cmd = [exe, str(script), "--scope", scope, "--repo-root", str(repo)]
        if include_airflow_home:
            cmd.append("--include-airflow-home")
        try:
            subprocess.run(
                cmd, cwd=str(repo), check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as exc:
            out = (exc.stdout or "").strip()
            err = (exc.stderr or "").strip()
            tail = "\n".join(x for x in (out[-2000:], err[-4000:]) if x)
            raise AirflowException(
                f"reset_project.py failed (exit {exc.returncode}). Output tail:\n{tail}"
            ) from exc

    return _run


_DEFAULT_ARGS = {
    "owner": "portfolio",
    "depends_on_past": False,
    "retries": 0,
}

for _scope in _RESET_SCOPES:
    _dag_id = "portfolio_reset_" + _scope.lower().replace(" ", "_")
    with DAG(
        dag_id=_dag_id,
        default_args=_DEFAULT_ARGS,
        description=f"Reset generated artifacts (scope={_scope}). Trigger only; schedule=None.",
        schedule=None,
        start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
        catchup=False,
        max_active_runs=1,
        tags=["reset", "maintenance", _scope.lower()],
    ) as _dag:
        PythonOperator(
            task_id="run_reset",
            python_callable=_make_reset_fn(_scope, include_airflow_home=False),
        )


def _include_airflow_home_reset_dag() -> bool:
    return os.environ.get("PORTFOLIO_INCLUDE_AIRFLOW_HOME_RESET_DAG", "false").lower() in (
        "1",
        "true",
        "yes",
    )


if _include_airflow_home_reset_dag():
    with DAG(
        dag_id="portfolio_reset_full_with_airflow_home",
        default_args=_DEFAULT_ARGS,
        description="Full reset including airflow/airflow_home. Dangerous; enable via PORTFOLIO_INCLUDE_AIRFLOW_HOME_RESET_DAG.",
        schedule=None,
        start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
        catchup=False,
        max_active_runs=1,
        tags=["reset", "maintenance", "full", "airflow_home"],
    ) as _dag_af:
        PythonOperator(
            task_id="run_reset",
            python_callable=_make_reset_fn("Full", include_airflow_home=True),
        )


def _weekly_reset_enabled() -> bool:
    return os.environ.get("PORTFOLIO_WEEKLY_RESET_SCOPE", "").strip()


_wscope = _weekly_reset_enabled()
if _wscope in _RESET_SCOPES:
    with DAG(
        dag_id="portfolio_reset_weekly_scheduled",
        default_args=_DEFAULT_ARGS,
        description=(
            f"Scheduled reset (scope={_wscope}) from PORTFOLIO_WEEKLY_RESET_SCOPE. "
            "Runs Sundays 04:00 UTC unless you change schedule below."
        ),
        schedule="0 4 * * 0",
        start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
        catchup=False,
        max_active_runs=1,
        tags=["reset", "maintenance", "scheduled"],
    ) as _dag_w:
        PythonOperator(
            task_id="run_reset",
            python_callable=_make_reset_fn(_wscope, include_airflow_home=False),
        )
