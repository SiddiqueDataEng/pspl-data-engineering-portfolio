# Concepts and purpose

This page answers **what** you are building, **why** each layer exists, and **how** the pieces relate. It complements the hands-on [LEARNING_GUIDE.md](LEARNING_GUIDE.md) (commands and troubleshooting) and the [README.md](../README.md) architecture diagram.

---

## 1. Purpose of this portfolio

The repository is a **local, open-source mirror** of a common humanitarian / INGO data stack: land diverse raw files, govern them through a **medallion** path, model **business-ready** tables with **dbt**, and expose **KPIs** to analysts.

You practice skills that transfer directly to **Databricks + Delta + dbt** in production:

- Ingesting **CSV.gz, Parquet, JSON, Avro** without losing lineage back to the file.
- Writing **Delta** tables so you get ACID writes, schema evolution, and time travel (in the Spark path).
- Separating **engineering transforms** (Silver cleaning, typed marts) from **ad-hoc analytics** (SQL files, dashboards).
- **Testing** at the Python boundary and inside dbt.

The **domain** is synthetic **Pakistani social protection** and **Afghan refugee** programme-style data (beneficiaries, payments, complaints, inventory, donors, surveys, protection). The numbers are fictional; the **grains, joins, and quality patterns** are realistic practice material.

---

## 2. Medallion architecture (Bronze → Silver → Gold)

### Bronze — “what landed”

**Purpose:** Preserve a faithful, queryable copy of what arrived from upstream, with minimal opinion. Bronze answers: *What did we receive, when, and in what shape?*

**In this repo:** `python ingest/ingest.py` reads files under `data_large/`, normalizes them into Spark DataFrames, and writes **Delta** under `delta_lake/bronze/`.

**Why Delta here:** Bronze is the handoff between **file diversity** (many libraries) and **downstream SQL/Spark**. Delta gives you a table abstraction over Parquet with transaction logs—closer to how cloud lakehouses store “raw” data than a pile of loose files.

### Silver — “trusted, analytics-ready entities”

**Purpose:** Apply **governance**: deduplicate, cast types, resolve keys, handle nulls, and encode business rules that everyone should agree on before metrics. Silver answers: *What do we believe is true about each entity at this grain?*

**In this repo:** `notebooks/delta_lake_operations.ipynb` reads Bronze Delta, cleans and promotes to `delta_lake/silver/`.

**Why a notebook (vs only dbt):** In many organizations, **heavy row-level Spark** (window functions, complex parsing) still lives in notebooks or jobs; dbt then consumes the **stable Silver contract**. This split matches that pattern and keeps dbt models simpler.

### Gold — “metrics and subject areas”

**Purpose:** Curate **marts** for consumption: star-ish shapes, KPI-ready joins, documented grains. Gold answers: *What does the business read every Monday?*

**In this repo:** dbt builds `stg_*` → `int_*` → `mart_*` and materializes marts as **tables in DuckDB** (`pspl.duckdb`). dbt reads Silver via **`delta_scan`** (DuckDB Delta extension), so Gold is still **logically** downstream of the lake—even though the query engine switches from Spark to DuckDB.

**Why DuckDB for Gold here:** It keeps the portfolio **lightweight** on a laptop while teaching the same dbt patterns (`ref`, `source`, tests, docs) you would run against Databricks SQL in production.

---

## 3. Why both Spark and DuckDB appear

| Concern | Spark + Delta (this repo) | DuckDB + dbt |
|--------|---------------------------|--------------|
| Scale-out, huge scans | Yes | Laptop-scale |
| Multi-format ingest to a lake | Yes | Possible but not the focus here |
| Cheap local modeling + tests | Heavy | Excellent |
| `delta_scan` from SQL | Native in Spark | Via DuckDB extension |

So: **Spark owns the lake writes**; **DuckDB owns the warehouse-shaped marts** for this demo. In production you might collapse some of this into Databricks-only, but the **separation of concerns** (lake vs warehouse) is still a common pattern.

---

## 4. dbt mental model (staging → intermediate → marts)

- **Staging (`stg_*`):** One-to-one with Silver sources, light renaming and type hygiene. Think “adapter layer” to your sources.
- **Intermediate (`int_*`):** Reusable building blocks—joins, aggregates, or bridges used by multiple marts.
- **Marts (`mart_*`):** Business-facing tables with clear grain (e.g. one row per district/program/month for payment KPIs).

**Why tests matter:** dbt tests encode **contracts** (“this key is unique”, “no nulls in this column”). They turn tribal knowledge into CI-friendly assertions—just like you want before promoting models in production.

---

## 5. KPI SQL and dashboards

The `sql/` folder holds **standalone queries** that read the same DuckDB objects dbt built. They demonstrate **window functions**, **CTEs**, and **reporting logic** without hiding inside a model.

The **Streamlit** app in `dashboard/streamlit_app.py` reads those marts too, but adds **interactive charts** for onboarding and stakeholder-style storytelling.

---

## 6. Environment variables that carry meaning

- **`DELTA_LAKE_PATH`:** Absolute path to the `delta_lake/` directory using **forward slashes**, required for dbt to parse `delta_scan('{{ env_var('DELTA_LAKE_PATH') }}/silver/...')` in `dbt/models/sources.yml`. The Windows pipeline script sets this for you.
- **`JAVA_HOME`:** Required for PySpark.
- **`HADOOP_HOME` / `winutils` (Windows):** Spark expects Hadoop-style filesystem hooks; the provided scripts configure this automatically.

---

## 7. From portfolio to interview narrative

A tight story:

1. **Ingest** multi-format sources to **Bronze Delta** with explicit readers and tests at the Python edge.
2. **Notebook** enforces **Silver** quality (dedupe, types) and documents Spark/Delta behavior including time travel.
3. **dbt** defines **versioned transformations** and tests from Silver to **Gold marts** in DuckDB—portable to `dbt-databricks` with adapter and path changes.
4. **KPIs + dashboard** show how analysts consume marts without re-implementing business logic.

That is a complete **lakehouse-shaped** arc on a laptop.

---

## Next steps

- **Scope and cloud mapping:** [SCOPE_AND_CLOUD.md](SCOPE_AND_CLOUD.md).
- Run the pipeline: [LEARNING_GUIDE.md — Section 5](LEARNING_GUIDE.md#5-step-by-step-setup-and-run-with-explanations).
- Commands in the browser: [getting-started.html](getting-started.html).
- Notebook environment: [JUPYTER_AND_NOTEBOOKS.md](JUPYTER_AND_NOTEBOOKS.md).
- Column-level detail: [data_dictionary.md](data_dictionary.md).
