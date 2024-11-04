# Scope and cloud alternatives

This page states **what this repository is for** (and what it is not), then maps the **local laptop stack** to common **cloud lakehouse** options so you can explain migrations and interview narratives.

For hands-on commands, see [RUN_EACH_COMPONENT.md](RUN_EACH_COMPONENT.md) and [LEARNING_GUIDE.md](LEARNING_GUIDE.md).

---

## Project scope

### In scope

- **Synthetic humanitarian-style data** for **Pakistani social protection** and **Afghan refugee** programme themes (beneficiaries, payments, complaints, inventory, donors, surveys, protection caseloads). Numbers and identities are **fictional**; grains and joins are realistic for engineering practice.
- **End-to-end lakehouse-shaped pipeline** on your machine: mixed-format files → **Bronze Delta** (PySpark) → **Silver Delta** (notebook) → **Gold marts** in **DuckDB** via **dbt** (`pspl` project, database file **`pspl.duckdb`** at repo root) → **KPI SQL** and **Streamlit**.
- **Quality and operations**: dbt tests, pytest (+ Hypothesis where used), runbooks, optional **Apache Airflow** (Docker recommended on Windows) to schedule dbt + SQL.
- **Learning artefacts**: documentation hub, trainer pack, slide manuscript ([training/TRAINER_SLIDES_WITH_SPEAKER_NOTES.md](training/TRAINER_SLIDES_WITH_SPEAKER_NOTES.md)), optional generated **PowerPoint** overview ([training/pspl_trainer_overview.pptx](training/pspl_trainer_overview.pptx) — regenerate with `scripts/generate_pspl_trainer_deck.py`).

### Out of scope

- **Official statistics**, PMT scores, or real beneficiary microdata — do not cite this repo as evidence in policy or funding decisions.
- **Production security**: no secrets management, row-level security, or multi-tenant isolation patterns beyond what a local demo needs.
- **Real-time streaming**, CDC, or low-latency ingestion — batch files and batch jobs only.
- **Cloud deployment** of this exact repo — the code is written for **local** paths (`delta_lake/`, `DELTA_LAKE_PATH`, `pspl.duckdb`). Moving to cloud means **re-pointing** sources, storage, and orchestration (see below), not “git push to production.”

---

## Local setup (summary)

| Layer | Local tool | Primary artifact |
|-------|------------|------------------|
| Raw | `data_large/` | Files (CSV.gz, Parquet, JSON, Avro) |
| Bronze | `ingest/ingest.py` | `delta_lake/bronze/` |
| Silver | `notebooks/delta_lake_operations.ipynb` | `delta_lake/silver/` |
| Gold | dbt (`dbt/profiles.yml` → `pspl.duckdb`) | Marts as DuckDB tables |
| Consume | `sql/*.sql`, `dashboard/streamlit_app.py` | KPIs, charts |
| Schedule (optional) | Airflow DAGs | `dbt_sql_daily`, optional full pipeline DAG |

---

## Cloud alternatives (local → production-style)

Use this table in interviews or migration discussions. The **pattern** stays the same; **SKUs and paths** change.

| Local (this repo) | Typical cloud analogue | What changes |
|-------------------|------------------------|--------------|
| Files in `data_large/` | **ADLS Gen2**, **S3**, **GCS** landing zones | Replace paths with cloud URIs (`abfss://`, `s3://`); IAM and networking. |
| `ingest/ingest.py` (PySpark) | **Databricks** notebook/job, **ADF** copy + **Synapse** Spark, **Glue** | Cluster config, secrets, partitions, idempotent writes to managed Delta. |
| Local Delta under `delta_lake/` | **Databricks Delta** on cloud storage + **Unity Catalog** | `delta_scan` paths become catalog + volume references; governance and ACLs. |
| DuckDB + **dbt-duckdb** | **Databricks SQL** / **Warehouse** + **dbt-databricks** | Adapter, `profiles.yml`, `source()` → UC tables or external locations; CI runs against a dev catalog. |
| `pspl.duckdb` | **Managed tables / semantic layer** in the warehouse | No single `.duckdb` file; marts live in the query engine’s metastore. |
| `sql/*.sql` + Streamlit | **SQL dashboards**, **Lakeview**, **Hex**, **Power BI / Tableau** on warehouse | Connection strings, extract vs live query, RLS. |
| `jupyter nbconvert` / local Spark | **Databricks Jobs** / **Workflows** | Attach cluster/job compute; parameters and retries. |
| Makefile / PowerShell scripts | **Databricks Workflows**, **ADF pipelines**, **Airflow** (managed or self-hosted) | Each local stage becomes a task; secrets via Key Vault / Databricks secrets. |
| Local **Airflow** (Docker) | **MWAA**, **Composer**, **ADF** orchestration, **Databricks Jobs** scheduler | Infra as code, SLAs, backfill strategy. |
| pytest / dbt tests | Same in **CI** (GitHub Actions, Azure DevOps) + optional **Databricks** integration tests | Spin up ephemeral warehouse or use fixed dev environment. |

---

## Naming: `pspl` and `pspl.duckdb`

- **`pspl`** is the **dbt project name** and **profile name** (`dbt_project.yml`, `profiles.yml`). Catalog/manifest nodes look like `model.pspl.<model_name>`.
- **`pspl.duckdb`** is the **on-disk DuckDB file** at the repository root (gitignored). Streamlit, KPI scripts, and Airflow DAGs expect this filename after `dbt run`.

---

## Migrating from `PSPL_portfolio.duckdb`

Older clones produced **`PSPL_portfolio.duckdb`** with dbt profile **`PSPL_portfolio`**. This repository now standardises on **`pspl.duckdb`** and the **`pspl`** dbt project/profile. Easiest path: run **`make clean`** or **`scripts/clean-artifacts.ps1`**, then rebuild with **`dbt run`**. Do not rename the old file unless you know the internal schema matches the current models.

---

## Related reading

- [CONCEPTS_AND_PURPOSE.md](CONCEPTS_AND_PURPOSE.md) — medallion mental model and why each layer exists  
- [README.md](../README.md) — architecture diagram and tool-mapping table  
- [training/README.md](training/README.md) — trainer pack and slide sources  
