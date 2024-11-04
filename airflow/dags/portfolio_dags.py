"""
Local Airflow DAGs: modular PySpark pipeline (ingest → notebook → dbt → KPI SQL) and daily dbt.

Assumes this file lives at ``<repo>/airflow/dags/portfolio_dags.py`` so the repository
root defaults to two levels above this file. Override with ``PORTFOLIO_REPO_ROOT``.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator

REPO_ROOT = Path(__file__).resolve().parents[2]


def _repo_root() -> Path:
    override = os.environ.get("PORTFOLIO_REPO_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return REPO_ROOT


def _delta_lake_path() -> str:
    return str((_repo_root() / "delta_lake").resolve()).replace("\\", "/")


def _base_subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env["DELTA_LAKE_PATH"] = _delta_lake_path()
    return env


def _linux_venv_candidates(repo: Path) -> list[Path]:
    """Prefer .venv-wsl when Airflow runs under WSL against a Windows-mounted repo."""
    return [
        repo / ".venv-wsl" / "bin" / "python",
        repo / ".venv" / "bin" / "python",
    ]


def _resolve_python_executable() -> str:
    repo = _repo_root()
    if sys.platform == "win32":
        candidate = repo / ".venv" / "Scripts" / "python.exe"
        if candidate.exists():
            return str(candidate)
    else:
        for candidate in _linux_venv_candidates(repo):
            if candidate.exists():
                return str(candidate)
    return sys.executable


def _resolve_dbt_executable() -> str:
    repo = _repo_root()
    if sys.platform == "win32":
        candidate = repo / ".venv" / "Scripts" / "dbt.exe"
        if candidate.exists():
            return str(candidate)
    else:
        for name in (".venv-wsl", ".venv"):
            candidate = repo / name / "bin" / "dbt"
            if candidate.exists():
                return str(candidate)
    return "dbt"


def _run_checked(
    cmd: list[str],
    *,
    cwd: str,
    env: dict[str, str] | None = None,
    label: str,
) -> None:
    """Run a subprocess; on failure raise AirflowException with stderr/stdout tail."""
    merged = _base_subprocess_env()
    if env:
        merged.update(env)
    try:
        subprocess.run(
            cmd,
            cwd=cwd,
            env=merged,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise AirflowException(f"{label}: command not found: {cmd[0]!r}") from exc
    except subprocess.CalledProcessError as exc:
        out = (exc.stdout or "").strip()
        err = (exc.stderr or "").strip()
        tail = "\n".join(x for x in (out[-2000:], err[-4000:]) if x)
        raise AirflowException(
            f"{label} failed with exit code {exc.returncode}. Output tail:\n{tail}"
        ) from exc


def _run_powershell_script(script_relative: str, label: str) -> None:
    repo = _repo_root()
    ps1 = repo / "scripts" / script_relative
    if not ps1.is_file():
        raise AirflowException(f"{label}: missing script {ps1}")
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ps1),
    ]
    _run_checked(cmd, cwd=str(repo), label=label)


def _run_bronze_ingest() -> None:
    repo = _repo_root()
    if sys.platform == "win32":
        _run_powershell_script("run-ingest.ps1", "Bronze ingest")
        return
    py = _resolve_python_executable()
    ingest = repo / "ingest" / "ingest.py"
    _run_checked([py, str(ingest)], cwd=str(repo), label="Bronze ingest")


def _run_silver_notebook() -> None:
    repo = _repo_root()
    if sys.platform == "win32":
        _run_powershell_script("run-spark-notebook.ps1", "Silver notebook")
        return
    py = _resolve_python_executable()
    nb = repo / "notebooks" / "delta_lake_operations.ipynb"
    out_dir = repo / "notebooks"
    cmd = [
        py,
        "-m",
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        str(nb),
        "--output-dir",
        str(out_dir),
        "--output",
        "delta_lake_operations_executed.ipynb",
    ]
    _run_checked(cmd, cwd=str(repo), label="Silver notebook")


def _sleep_after_spark() -> None:
    """Mirror scripts/run-full-pipeline.ps1 handle release before dbt."""
    time.sleep(5)


def _run_dbt_run() -> None:
    repo = _repo_root()
    _run_checked(
        [_resolve_dbt_executable(), "run"],
        cwd=str(repo / "dbt"),
        label="dbt run",
    )


def _run_dbt_test() -> None:
    repo = _repo_root()
    _run_checked(
        [_resolve_dbt_executable(), "test"],
        cwd=str(repo / "dbt"),
        label="dbt test",
    )


def _run_sql_kpis() -> None:
    try:
        import duckdb
    except ImportError as exc:
        raise AirflowException(
            "duckdb package is required for the KPI SQL task. Install project requirements in the Airflow environment."
        ) from exc

    repo = _repo_root()
    db_path = repo / "pspl.duckdb"
    if not db_path.exists():
        raise AirflowException(
            f"Missing DuckDB database {db_path}. Run bronze ingest, the Silver notebook, and dbt first "
            "(e.g. portfolio_full_pipeline_weekly DAG or scripts/run-full-pipeline.ps1)."
        )
    sql_dir = repo / "sql"
    if not sql_dir.is_dir():
        raise AirflowException(f"Missing SQL directory {sql_dir}")
    try:
        con = duckdb.connect(str(db_path))
    except Exception as exc:
        raise AirflowException(f"Could not open DuckDB at {db_path}: {exc}") from exc
    try:
        for sql_file in sorted(sql_dir.glob("*.sql")):
            try:
                con.execute(sql_file.read_text(encoding="utf-8"))
            except Exception as exc:
                raise AirflowException(f"KPI SQL failed in {sql_file.name}: {exc}") from exc
    finally:
        con.close()


def _run_full_portfolio_pipeline() -> None:
    """Single-shot pipeline (used only when the optional monolithic DAG is enabled)."""
    repo = _repo_root()
    if sys.platform == "win32":
        ps1 = repo / "scripts" / "run-full-pipeline.ps1"
        _run_checked(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(ps1),
            ],
            cwd=str(repo),
            label="Full PowerShell pipeline",
        )
    else:
        _run_checked(["make", "all"], cwd=str(repo), label="make all")


def _include_full_pipeline_dag() -> bool:
    return os.environ.get("PORTFOLIO_INCLUDE_FULL_PIPELINE_DAG", "false").lower() in (
        "1",
        "true",
        "yes",
    )


_DEFAULT_ARGS = {
    "owner": "portfolio",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="dbt_sql_daily",
    default_args=_DEFAULT_ARGS,
    description="dbt run + test and KPI SQL files against pspl.duckdb",
    schedule="0 6 * * *",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    tags=["dbt", "duckdb", "sql"],
) as dag_dbt_sql:
    t_dbt_run = PythonOperator(task_id="dbt_run", python_callable=_run_dbt_run)
    t_dbt_test = PythonOperator(task_id="dbt_test", python_callable=_run_dbt_test)
    t_sql_kpis = PythonOperator(task_id="sql_kpis", python_callable=_run_sql_kpis)
    t_dbt_run >> t_dbt_test >> t_sql_kpis

with DAG(
    dag_id="portfolio_full_pipeline_weekly",
    default_args=_DEFAULT_ARGS,
    description="Bronze ingest → Silver notebook → dbt → KPI SQL (modular tasks; Windows uses PowerShell helpers)",
    schedule="0 5 * * 0",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["ingest", "spark", "dbt", "full"],
) as dag_modular_full:
    t_ingest = PythonOperator(task_id="bronze_ingest", python_callable=_run_bronze_ingest)
    t_notebook = PythonOperator(task_id="silver_notebook", python_callable=_run_silver_notebook)
    t_pause = PythonOperator(task_id="wait_for_delta_handles", python_callable=_sleep_after_spark)
    t_dbt_run = PythonOperator(task_id="dbt_run", python_callable=_run_dbt_run)
    t_dbt_test = PythonOperator(task_id="dbt_test", python_callable=_run_dbt_test)
    t_sql = PythonOperator(task_id="sql_kpis", python_callable=_run_sql_kpis)
    t_ingest >> t_notebook >> t_pause >> t_dbt_run >> t_dbt_test >> t_sql

if _include_full_pipeline_dag():
    with DAG(
        dag_id="portfolio_full_pipeline_monolith",
        default_args=_DEFAULT_ARGS,
        description="One task: full pipeline script (Windows: PowerShell; Unix: make all)",
        schedule=None,
        start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
        catchup=False,
        max_active_runs=1,
        tags=["ingest", "spark", "dbt", "full", "legacy"],
    ) as dag_monolith:
        PythonOperator(
            task_id="run_full_pipeline",
            python_callable=_run_full_portfolio_pipeline,
        )
