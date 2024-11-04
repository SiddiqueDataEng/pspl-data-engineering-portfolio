# Canonical per-component run reference

Single place to run **one** pipeline stage at a time: **Windows** (`scripts/*.ps1` or `run-component.ps1`) and **macOS/Linux** (`make` or shell). For first-time setup (venv, Java, `DELTA_LAKE_PATH`, execution policy), use [LEARNING_GUIDE.md](LEARNING_GUIDE.md) **Section 5**.

**Typical order:** data under `data_large/` → Bronze Delta → Silver Delta → dbt → KPI SQL → dashboard. **Airflow** and **dbt docs** are optional and can run whenever dependencies for that stage are satisfied.

---

## Dispatcher (Windows)

From repo root (after `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` if needed):

```powershell
.\scripts\run-component.ps1 <name>
```

Valid **`<name>`** values: `datagenerator`, `ingest`, `spark-notebook`, `dbt-run`, `dbt-test`, `dbt-docs`, `sql-kpis`, `dashboard`, `airflow-docker`, `airflow-standalone`.

For extra arguments to dbt, use PowerShell’s stop-parsing token or call the underlying script, for example:

```powershell
.\scripts\run-component.ps1 dbt-run --% --select mart_payments
```

---

## Per-component matrix

| # | Component | Role | Windows (repo root) | macOS / Linux (repo root) | Verify success | Depends on |
|---|-----------|------|------------------------|---------------------------|----------------|------------|
| 0 | **Synthetic data** | Regenerate `data_large/` | `.\scripts\run-component.ps1 datagenerator` or `.\scripts\run-datagenerator.ps1` | `make datagenerator` or `python datagenerator.py` | Nine files under `data_large/` (see root README tree) | Python venv; optional if repo already has data |
| 1 | **Bronze ingest** | PySpark → Delta Bronze | `.\scripts\run-component.ps1 ingest` or `.\scripts\run-ingest.ps1` | `make ingest` or `python ingest/ingest.py` | Directories under `delta_lake/bronze/<table>/` | `data_large/`; Java + Spark (see LEARNING_GUIDE) |
| 2 | **Silver notebook** | PySpark Bronze → Silver | `.\scripts\run-component.ps1 spark-notebook` or `.\scripts\run-spark-notebook.ps1` | `make spark-transform` | Directories under `delta_lake/silver/<table>/` | Bronze tables from step 1 |
| 3 | **dbt run** | Staging → marts in DuckDB | `.\scripts\run-component.ps1 dbt-run` or `.\scripts\run-dbt-run.ps1` | `make dbt-run` | `pspl.duckdb` at repo root; `dbt run` exit 0 | Silver Delta; **`DELTA_LAKE_PATH`** set to repo `delta_lake` (Makefile sets it; scripts set it—see LEARNING_GUIDE if calling `dbt` manually) |
| 4 | **dbt test** | Data tests | `.\scripts\run-component.ps1 dbt-test` or `.\scripts\run-dbt-test.ps1` | `make dbt-test` | All tests pass | Step 3 completed |
| 5 | **KPI SQL** | Run `sql/*.sql` on DuckDB | `.\scripts\run-component.ps1 sql-kpis` or `.\scripts\run-sql-kpis.ps1` | `make sql-kpis` | Query output in terminal | **`pspl.duckdb`** from step 3; **DuckDB CLI** on `PATH` for Unix `make sql-kpis` |
| 6 | **Streamlit dashboard** | KPI UI over marts | `.\scripts\run-component.ps1 dashboard` or `.\scripts\run-dashboard.ps1` | `make dashboard` or `streamlit run dashboard/streamlit_app.py` | Browser opens; charts load | Step 3 (marts present) |
| 7 | **dbt docs** | Lineage site (blocks) | `.\scripts\run-component.ps1 dbt-docs` or `.\scripts\run-dbt-docs.ps1` | `make dbt-docs` | `dbt docs serve` running; browser | Same as dbt run for parse; default port **8080** may clash with Airflow |
| 8a | **Airflow (Docker)** | Scheduler + UI in containers | `.\scripts\run-component.ps1 airflow-docker` or `.\scripts\run-airflow-docker.ps1` | `make docker-airflow-up` or `docker compose -f docker-compose.airflow.yml up` | [http://localhost:8080](http://localhost:8080); DAGs visible | Docker; repo mounted in compose; **recommended on Windows** |
| 8b | **Airflow (venv)** | Native `airflow standalone` | `.\scripts\run-component.ps1 airflow-standalone` or `.\scripts\airflow-standalone.ps1` | `make airflow-standalone` (after install) | UI at **8080**; admin password in console or `airflow/airflow_home/` | **`./scripts/install-airflow.sh`** or **`.\scripts\install-airflow.ps1`** first; **not supported on native Windows**—use Docker or WSL |

---

## One-time installs (Airflow only)

| Action | Windows | macOS / Linux |
|--------|---------|----------------|
| Install Airflow into `.venv` | `.\scripts\install-airflow.ps1` | `./scripts/install-airflow.sh` or `make airflow-install` |

---

## Tests and clean (not pipeline stages)

| Action | Windows | macOS / Linux |
|--------|---------|----------------|
| pytest | `.venv\Scripts\pytest.exe tests/ -v` (or activate venv first) | `make test` or `pytest tests/ -v` |
| Remove generated lake + DuckDB + dbt `target/` | `.\scripts\clean-artifacts.ps1` | `make clean` |

---

## Related documents

- [README.md](README.md) — documentation hub and onboarding path  
- [LEARNING_GUIDE.md](LEARNING_GUIDE.md) — Section 5 setup; Section 9 debugging  
- [runbooks/ingestion_runbook.md](runbooks/ingestion_runbook.md), [runbooks/dbt_runbook.md](runbooks/dbt_runbook.md) — operations detail  
- [../README.md](../README.md) — architecture and Airflow DAG summary  
