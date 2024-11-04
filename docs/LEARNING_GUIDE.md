# Learning guide: Pakistani social protection data engineering portfolio

This document is the **canonical learning path** for the repository. It explains what the project is, how each part fits together, what to run in which order, and how it maps to real lakehouse work (for example Databricks and dbt in production).

**New here?** Start with the story and document map in [`docs/README.md`](README.md), then the concepts page [`CONCEPTS_AND_PURPOSE.md`](CONCEPTS_AND_PURPOSE.md), then return here for **hands-on** setup (**Section 5**).

For a **clickable command reference** (copy/paste for Windows and Bash), open [`getting-started.html`](getting-started.html) in a browser from the `docs/` folder, or from the repo root: `start docs\getting-started.html` (Windows) / `open docs/getting-started.html` (macOS).

---

## 1. What you are learning

This repo is a **self-contained data engineering portfolio** that exercises:

| Skill | Where it appears |
|--------|------------------|
| Multi-format ingestion (CSV.gz, Parquet, JSON, Avro) | `ingest/readers.py`, `ingest/ingest.py` |
| Medallion architecture (Bronze → Silver → Gold) | `delta_lake/`, `notebooks/`, `dbt/models/` |
| PySpark + Delta Lake (local) | `ingest/ingest.py`, `notebooks/delta_lake_operations.ipynb` |
| dbt (staging → intermediate → marts) | `dbt/models/` |
| Analytics SQL (KPIs, window functions, CTEs) | `sql/*.sql` |
| Interactive KPI storytelling | `dashboard/streamlit_app.py`, `notebooks/00_onboarding_tour.ipynb` |
| Tests (unit + property-based) | `tests/` |
| Operational runbooks | `docs/runbooks/` |

The **domain** is synthetic **Pakistani social protection** and **Afghan refugee** humanitarian-style data (beneficiaries, payments, complaints, inventory, donors, surveys, protection caseloads). The numbers are fake; the **patterns** (grain, joins, quality checks) are what you practice.

---

## 2. End-to-end mental model

1. **Sources** live under `data_large/` (nine files, mixed formats).
2. **Bronze**: `python ingest/ingest.py` reads each file with the right library, builds Spark DataFrames, writes **Delta** tables under `delta_lake/bronze/`.
3. **Silver**: the Jupyter notebook `notebooks/delta_lake_operations.ipynb` reads Bronze Delta, cleans/dedupes/casts, writes **Silver** Delta under `delta_lake/silver/`.
4. **Gold (dbt)**: dbt treats Silver Delta paths as **sources**, builds `stg_*` → `int_*` → `mart_*`, and materializes into **DuckDB** (`pspl.duckdb` at repo root by default). See `dbt/models/sources.yml` and `dbt/profiles.yml`.
5. **KPIs**: standalone SQL in `sql/` runs against that DuckDB database (same marts/staging exposed as DuckDB views/tables depending on your project config).

So: **files → Delta (Spark) → Delta (Spark) → DuckDB (dbt) → ad-hoc SQL**.

The main [`README.md`](../README.md) includes a Mermaid diagram of this flow; keep it open while you trace one dataset from file to mart.

**Why order matters:** dbt reads **Silver** Delta paths. The notebook needs **Bronze** first. Ingest creates Bronze. KPI SQL expects **DuckDB** built by dbt. Skipping a stage produces missing-path or missing-database errors that look unrelated until you map them to this chain.

---

## 3. Repository map (what each folder is for)

| Path | Role |
|------|------|
| `data_large/` | Raw synthetic inputs (not regenerated in CI by default). |
| `ingest/` | Bronze pipeline: readers, transforms, `ingest.py` CLI. |
| `delta_lake/bronze/` | Raw-ish Delta tables after ingestion. Often gitignored. |
| `delta_lake/silver/` | Cleaned Delta after the notebook. Often gitignored. |
| `notebooks/` | PySpark Bronze→Silver + exploration and charts. |
| `dbt/` | dbt project: `sources.yml`, staging/intermediate/marts, tests, macros. |
| `sql/` | Seven KPI queries documented to run with DuckDB CLI. |
| `docs/runbooks/` | Day-2 operations: ingestion and dbt. |
| `docs/sample_outputs/` | Example query outputs and artifacts for portfolio display. |
| `tests/` | pytest + Hypothesis; includes Spark integration-style tests. |
| `Makefile` | Unix-friendly orchestration (`make all`, `make ingest`, …). |
| `scripts/` | Windows helpers: full pipeline, SQL KPIs, clean artifacts. |
| `setup.ps1` | Windows: create `.venv`, install `requirements.txt`, prefer Python 3.11. |
| `setup_java17.ps1` | Windows: optional Temurin 17 via winget (elevated). |

---

## 4. Prerequisites (read before first run)

- **Python 3.10–3.12 (prefer 3.11)** — `requirements.txt` is pinned for these versions. **3.14+** often breaks wheels or Spark-related tests; use `py -3.11` and `.\setup.ps1 -Python "py -3.11"`.
- **Java 11 or 17** — PySpark runs on the JVM. Set **`JAVA_HOME`** to a JDK install. On Windows, Eclipse Temurin under `C:\Program Files\Eclipse Adoptium\jdk-17*` is common; `setup_java17.ps1` can install it if you use winget as admin.
- **Network** — First Spark run downloads Delta JARs from Maven; `run-full-pipeline.ps1` may download **winutils.exe** once for Hadoop-on-Windows.
- **DuckDB CLI** — Needed for `make sql-kpis` and `scripts/run-sql-kpis.ps1` (KPI step). [Install DuckDB](https://duckdb.org/docs/installation/) and ensure `duckdb` is on `PATH`.

---

## 5. Step-by-step setup and run (with explanations)

Use this checklist the first time and whenever you recreate the machine or clone fresh.

### Step 0 — Open a shell in the repository root

**What:** Your current directory must be the folder that contains `ingest/`, `dbt/`, `data_large/`, and `requirements.txt`.

**Why:** All relative paths (`data_large`, `delta_lake`, `dbt/profiles.yml` pointing at `../pspl.duckdb`) assume the repo root.

**How (PowerShell):**

```powershell
cd "C:\Users\<you>\Desktop\Pakistani social protection landscape"
```

---

### Step 1 — Allow local scripts (Windows PowerShell only)

**What:** Relax execution policy for **this process** so `.ps1` files can run.

**Why:** Default Windows policy blocks `setup.ps1`, `Activate.ps1`, and `scripts/*.ps1`.

**How:**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Optional persistent fix for your user only:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

### Step 2 — Install Python 3.11 (if `py -3.11` is missing)

**What:** Install CPython 3.11 using the **Python launcher**.

**Why:** A stable 3.11 venv matches the pinned wheels (pandas, matplotlib, PySpark) and avoids “no module named pip” / broken venv issues seen on mixed upgrades.

**How:**

```powershell
py install 3.11
```

---

### Step 3 — Create the virtual environment and install dependencies

**What:** `setup.ps1` creates `.venv`, upgrades pip, and runs `pip install -r requirements.txt` (with `--prefer-binary` to prefer wheels on Windows).

**Why:** Isolates project packages from your global Python (which might be 3.14 and lack `pandas` / `dbt` for this repo).

**How:**

```powershell
.\setup.ps1 -Force -Python "py -3.11"
```

Wait until it prints **Done.** If pip fails on matplotlib, the repo pins `matplotlib==3.8.4` for Windows wheels; pull the latest `requirements.txt` if yours is older.

---

### Step 4 — Activate the virtual environment

**What:** Put `.venv\Scripts` first on `PATH` for this terminal session.

**Why:** Ensures `python`, `pip`, `jupyter`, and `dbt` resolve to the project versions. The pipeline script can call `.venv\Scripts\python.exe` directly, but activating keeps **your** manual commands consistent.

**How:**

```powershell
.\.venv\Scripts\Activate.ps1
```

Prompt should show `(.venv)`.

---

### Step 5 — Confirm Java for Spark

**What:** JDK 17 (or 11) available and **`JAVA_HOME`** set, or discoverable by helper scripts.

**Why:** PySpark is a JVM process; without Java, SparkSession never starts.

**How:**

```powershell
java -version
```

If needed (one-off check script):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\setup_java17.ps1"
```

---

### Step 6 — Understand Windows-only Spark pieces (automatic in `run-full-pipeline.ps1`)

**What:**

- **`HADOOP_HOME`** — Folder Spark treats as a minimal Hadoop home.
- **`winutils.exe`** — Small Windows helper in `%HADOOP_HOME%\bin` so Spark can set file permissions like on Linux.

**Why:** Without them, Spark often fails with `HADOOP_HOME and hadoop.home.dir are unset` or `Did not find winutils.exe`.

**How:** `scripts/run-full-pipeline.ps1` sets `HADOOP_HOME` to `%USERPROFILE%\hadoop`, downloads **winutils** from the usual community repo if missing, and prepends `bin` to `PATH`. For pytest only, see `run_tests.ps1` for the same pattern.

---

### Step 7 — Environment variable for dbt Delta paths

**What:** **`DELTA_LAKE_PATH`** must point at the folder that contains **`silver`** and **`bronze`** — i.e. the **`delta_lake`** directory, using **forward slashes** on Windows so SQL strings stay portable.

**Why:** `dbt/models/sources.yml` uses `delta_scan('{{ env_var('DELTA_LAKE_PATH') }}/silver/...')`. If unset, dbt fails at parse time with `Env var required but not provided: 'DELTA_LAKE_PATH'`.

**How:** `scripts/run-full-pipeline.ps1` sets this for you. For **manual** dbt:

```powershell
$env:DELTA_LAKE_PATH = ($PWD.Path + "\delta_lake").Replace("\", "/")
cd dbt
dbt run
```

(Adjust `$PWD` if you are not in the repo root.)

---

### Step 8 — Run the full pipeline (choose one path)

#### Path A — Windows (recommended on your machine)

**What:** One script runs: ingest → notebook → dbt run/test → KPI SQL.

**Why:** Sets Java discovery, Hadoop/winutils, `DELTA_LAKE_PATH`, and uses `.venv\Scripts\python.exe` so you do not accidentally use global Python 3.14.

**How:**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\run-full-pipeline.ps1
```

The script **stops with a non-zero exit code** if ingest, notebook, dbt, or KPI steps fail (so CI or scripts can detect failure).

#### Path B — macOS / Linux with Make

**What:** Same stages via `Makefile`.

**Why:** Closer to how teams orchestrate with CI or Airflow-style steps.

**How:**

```bash
make all
```

---

### Step 9 — Run stages one at a time (learning and debugging)

Use this when you want to see **where** something broke. For a **full Windows vs Unix matrix** (every script, verify column, Airflow), see [`RUN_EACH_COMPONENT.md`](RUN_EACH_COMPONENT.md).

| Step | Command (repo root, venv active) | What you should see |
|------|----------------------------------|------------------------|
| 1 Bronze | `python ingest/ingest.py` | Folders under `delta_lake/bronze/<table>` |
| 2 Silver | `python -m jupyter nbconvert --to notebook --execute notebooks/delta_lake_operations.ipynb --output-dir notebooks --output delta_lake_operations_executed.ipynb --output-dir notebooks --output delta_lake_operations_executed.ipynb` | `delta_lake/silver/<table>` |
| 3 Gold | `cd dbt` then `dbt run` / `dbt test` (with `DELTA_LAKE_PATH` set) | `pspl.duckdb` at repo root |
| 4 KPIs | `.\scripts\run-sql-kpis.ps1` (Windows) or `make sql-kpis` (Unix) | Query output in the terminal |

**Tip:** Limit Spark work while learning: `python ingest/ingest.py --dataset beneficiaries` (see `ingest.py --help`).

---

### Step 10 — Verify and explore

**What:** Confirm artifacts exist.

**Why:** Teaches you which layer owns which files (medallion debugging skill).

**Checklist:**

- `delta_lake/bronze/` populated after ingest.
- `delta_lake/silver/` populated after the notebook.
- `pspl.duckdb` exists after `dbt run`.
- Open `dbt docs` (`cd dbt` → `dbt docs generate` → `dbt docs serve`) for lineage.

---

### Step 11 — Story-led exploration (Jupyter + Streamlit)

**What:** After the pipeline succeeds, open **`notebooks/00_onboarding_tour.ipynb`** in JupyterLab for a guided narrative (no Spark required to read the story cells), then **`notebooks/delta_lake_operations.ipynb`** for the Spark/Delta deep dive. For interactive KPI charts over the same DuckDB marts, run **`streamlit run dashboard/streamlit_app.py`** from the repo root (Windows helper: `.\scripts\run-dashboard.ps1`).

**Why:** Separates **onboarding** (vocabulary and folder map) from **execution** (heavy Spark notebook) and **stakeholder-style** visuals (Streamlit) without re-running SQL by hand.

**How:** With `.venv` active: `python -m jupyter lab`, or see [`JUPYTER_AND_NOTEBOOKS.md`](JUPYTER_AND_NOTEBOOKS.md).

---

## 6. Recommended learning order (concepts after first run)

1. Read [`docs/README.md`](README.md) and [`docs/CONCEPTS_AND_PURPOSE.md`](CONCEPTS_AND_PURPOSE.md), then [`README.md`](../README.md) architecture and tool-mapping table (local vs cloud).
2. Skim [`docs/data_dictionary.md`](data_dictionary.md) for column meanings and grains.
3. Open [`notebooks/00_onboarding_tour.ipynb`](../notebooks/00_onboarding_tour.ipynb) (story map) before stepping through `delta_lake_operations.ipynb`.
4. Run **ingest** for one dataset to limit Spark work:  
   `python ingest/ingest.py --dataset beneficiaries` (see `ingest.py --help`).
5. Open the **notebook** and run cells stepwise; relate each step to Silver table quality (nulls, duplicates, types).
6. Run **dbt** with `dbt run --select stg_beneficiaries+` (example) to learn the DAG incrementally, then full `dbt run`.
7. Pick **one** file in `sql/`, read the header comment, run it, compare to [`docs/sample_outputs/`](sample_outputs/).
8. Read **tests**: `tests/test_transformations.py` for pure Python; `tests/test_ingestion.py` for Spark boundaries.
9. Read **runbooks**: [`ingestion_runbook.md`](runbooks/ingestion_runbook.md), [`dbt_runbook.md`](runbooks/dbt_runbook.md).
10. Launch the **Streamlit** dashboard (`.\scripts\run-dashboard.ps1`) to connect KPI visuals back to the marts.

---

## 7. Commands cheat sheet

### Full pipeline (Bash + Make, from repo root)

```bash
pip install -r requirements.txt
export DELTA_LAKE_PATH="$(pwd)/delta_lake"   # forward slashes; required for dbt parse
python ingest/ingest.py
python -m jupyter nbconvert --to notebook --execute notebooks/delta_lake_operations.ipynb --output-dir notebooks --output delta_lake_operations_executed.ipynb
cd dbt && dbt run && dbt test && cd ..
make sql-kpis    # requires duckdb CLI and Unix shell loop; see scripts on Windows
```

One-shot: `make all` (ensure `DELTA_LAKE_PATH` is set in your shell if you run `dbt` manually; the Makefile may not set it—use the export above when needed).

### Tests

```bash
pytest tests/ -v
```

### dbt docs

```bash
cd dbt && dbt docs generate && dbt docs serve
```

### Clean generated artifacts

```bash
make clean
```

On **Windows PowerShell**, use [`scripts/run-sql-kpis.ps1`](../scripts/run-sql-kpis.ps1) and [`scripts/run-full-pipeline.ps1`](../scripts/run-full-pipeline.ps1) instead of `make` where noted in [`getting-started.html`](getting-started.html).

---

## 8. How this maps to a job interview or real PSPL-style stack

- **Ingest** ≈ ADF-triggered notebook or Spark job landing raw data to Bronze.
- **Notebook Silver** ≈ governed cleaning jobs (DQ rules, SCD patterns later).
- **dbt** ≈ the same repo you would run in CI against Databricks SQL / Unity Catalog with adapter changes.
- **KPI SQL** ≈ analyst-facing queries or semantic layer prototypes.

When you explain the project, emphasize **lineage** (sources.yml → stg → int → mart), **tests** (dbt tests + pytest), and **operability** (runbooks, idempotent runs, clean target).

---

## 9. Troubleshooting

| Symptom | Things to check |
|---------|------------------|
| `running scripts is disabled` | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` (or use `.venv\Scripts\python.exe -m pip ...` / `python -m streamlit run ...` without activating). |
| `pip` builds **pandas** from source / Meson / `vswhere.exe` missing | You are probably on **Python 3.13+** (e.g. 3.14) without wheels. Recreate the venv with **3.11**: `.\setup.ps1 -Force -Python "py -3.11"`, then only use `.venv\Scripts\python.exe -m pip` (never bare `pip` on PATH). |
| `No module named 'pandas'` / `dbt` / `jupyter_core` | Recreate venv: `.\setup.ps1 -Force -Python "py -3.11"`. Do not mix global `python` 3.14 with this project. |
| `No module named pip` inside `.venv` | Delete `.venv`, rerun `py -3.11 -m venv .venv`, then `setup.ps1`. |
| `HADOOP_HOME` / `winutils` errors | Run `.\scripts\run-full-pipeline.ps1` (sets paths) or mirror `run_tests.ps1`. |
| `Env var required but not provided: 'DELTA_LAKE_PATH'` | Set to repo `delta_lake` with forward slashes; `run-full-pipeline.ps1` sets this automatically. |
| `JAVA_HOME is not set` / Spark fails to start | Install JDK 11/17; set `JAVA_HOME`; restart shell. |
| Maven / JAR download errors | Corporate firewall; run on open network or configure Nexus mirror. |
| dbt cannot find Delta / `DELTA_TABLE_NOT_FOUND` | Run ingest + notebook so Bronze/Silver exist; check `DELTA_LAKE_PATH`. |
| DuckDB file missing | Run `dbt run` first so `pspl.duckdb` is created at repo root. |
| `make sql-kpis` fails on Windows | Use `.\scripts\run-sql-kpis.ps1` or Git Bash; `Makefile` uses a Bash `for` loop. |
| `FileNotFoundError` for `notebooks\\notebooks\\delta_lake_operations_executed.ipynb` | **`--output notebooks/...` is wrong:** nbconvert treats `--output` as relative to the notebook’s folder. Use **`--output-dir notebooks --output delta_lake_operations_executed.ipynb`** (see `JUPYTER_AND_NOTEBOOKS.md`) or **`.\scripts\run-spark-notebook.ps1`**. |
| Hypothesis / PySpark flaky tests | Prefer Python 3.11 venv; Spark + Hypothesis can be sensitive on very new Python. |
| PowerShell parse errors in `.ps1` | Re-save scripts as UTF-8 without smart quotes; do not paste error text into the shell as commands. |

---

## 10. Extending the project (exercises)

- Add a **new dbt test** on `mart_payment_kpis` for a business rule you define.
- Add a **documentation paragraph** in `schema.yml` for one staging model (ownership, grain, refresh).
- Add a **new KPI SQL** file and a matching row in `docs/sample_outputs/`.
- Parameterize **ingest** `--data-dir` to point at a copy of `data_large/` to practice path hygiene.

---

## 11. Related files

- [README.md](../README.md) — overview, diagram, quick start.
- [RUN_EACH_COMPONENT.md](RUN_EACH_COMPONENT.md) — canonical per-component commands (Windows vs Unix).
- [README.md](README.md) — documentation hub (onboarding path and document map).
- [training/README.md](training/README.md) — **trainer pack:** curriculum, master technical guide, slide outline.
- [CONCEPTS_AND_PURPOSE.md](CONCEPTS_AND_PURPOSE.md) — why each layer exists.
- [JUPYTER_AND_NOTEBOOKS.md](JUPYTER_AND_NOTEBOOKS.md) — JupyterLab, notebooks, Streamlit.
- [getting-started.html](getting-started.html) — UI with copyable commands.
- [data_dictionary.md](data_dictionary.md) — columns and entities.
- [runbooks/ingestion_runbook.md](runbooks/ingestion_runbook.md), [runbooks/dbt_runbook.md](runbooks/dbt_runbook.md) — operations.

When in doubt, run a **single stage** (ingest only, or dbt only), confirm outputs on disk or in DuckDB, then proceed. Incremental validation is how pipelines are debugged in production too.
