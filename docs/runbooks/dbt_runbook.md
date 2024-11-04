# dbt Project Runbook

This runbook covers how to run, test, and document the `pspl` dbt project, how to interpret test failures, and how to add new models following the project's layered architecture.

**Validates: Requirements 5.6**

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | Check with `python --version` |
| dbt-core | 1.7+ | Installed via `requirements.txt` |
| dbt-duckdb | 1.7+ | DuckDB adapter for dbt |
| DuckDB | 0.10+ | Embedded; no separate server needed |
| Silver Delta tables | — | Must exist at `delta_lake/silver/` before running dbt |

Install Python dependencies from the repo root:

```bash
pip install -r requirements.txt
```

The Silver Delta tables are produced by the PySpark notebook (`notebooks/delta_lake_operations.ipynb`). Run the ingestion pipeline and the notebook before executing any dbt commands. See `docs/runbooks/ingestion_runbook.md` for ingestion steps.

---

## Environment Setup

### DELTA_LAKE_PATH

The dbt project reads Silver Delta tables via DuckDB's `delta_scan()` function. The `sources.yml` file references `{{ env_var('DELTA_LAKE_PATH') }}` to locate the Delta Lake root. Set this variable before running any dbt command:

**macOS / Linux:**

```bash
export DELTA_LAKE_PATH=$(pwd)/delta_lake
```

**Windows (PowerShell):**

```powershell
$env:DELTA_LAKE_PATH = "$PWD\delta_lake"
```

Verify the path resolves to the directory containing `bronze/` and `silver/` subdirectories:

```bash
ls $DELTA_LAKE_PATH/silver/
# Expected: beneficiaries  payments  surveys  inventory  complaints
#           donor_reports  afghan_refugees  refugee_assistance  refugee_protection
```

### Profile and target

The dbt profile is defined in `dbt/profiles.yml`:

```yaml
pspl:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: ../pspl.duckdb
      threads: 1
      extensions:
        - delta
```

The DuckDB database file is written to `pspl.duckdb` at the repository root (one level above `dbt/`). All dbt commands must be run from the `dbt/` directory so that the relative path resolves correctly.

```bash
cd dbt/
```

---

## Running dbt run

Execute all models in dependency order:

```bash
dbt run
```

### Expected output

A successful run produces output similar to:

```
Running with dbt=1.7.x
Found 16 models, 2 tests, 0 snapshots, 0 analyses, 1 macro, 0 operations,
       0 seed files, 9 sources, 0 exposures, 0 metrics

Concurrency: 4 threads (target='dev')

1 of 16 START sql view model staging.stg_afghan_refugees .................. [RUN]
2 of 16 START sql view model staging.stg_beneficiaries .................... [RUN]
3 of 16 START sql view model staging.stg_complaints ....................... [RUN]
4 of 16 START sql view model staging.stg_donor_reports .................... [RUN]
...
9 of 16 START sql view model staging.stg_surveys .......................... [RUN]
10 of 16 START sql view model intermediate.int_beneficiaries_payments ..... [RUN]
11 of 16 START sql view model intermediate.int_donor_program_aggregates ... [RUN]
12 of 16 START sql view model intermediate.int_refugees_assistance ........ [RUN]
13 of 16 START sql table model marts.mart_donor_budget_vs_actual .......... [RUN]
14 of 16 START sql table model marts.mart_payment_kpis .................... [RUN]
15 of 16 START sql table model marts.mart_protection_caseload ............. [RUN]
16 of 16 START sql table model marts.mart_refugee_assistance_summary ...... [RUN]

Finished running 9 view models, 4 table models in X.XXs.

Completed successfully

Done. PASS=16 WARN=0 ERROR=0 SKIP=0 TOTAL=16
```

Key things to confirm:
- **PASS=16** — all 16 models built without errors.
- **ERROR=0** — no model failed to compile or execute.
- Staging and intermediate models are materialized as **views**; mart models are materialized as **tables** (as configured in `dbt_project.yml`).
- Elapsed time is typically under 30 seconds on the synthetic dataset.

### Running a subset of models

Run a single model and all its upstream dependencies:

```bash
dbt run --select +mart_payment_kpis
```

Run only the staging layer:

```bash
dbt run --select staging
```

Run only the marts layer:

```bash
dbt run --select marts
```

---

## Running dbt test

Execute all schema tests and singular tests:

```bash
dbt test
```

### Expected output

A clean run with zero failures looks like:

```
Running with dbt=1.7.x
Found 16 models, 2 tests, 0 snapshots, ...

Concurrency: 4 threads (target='dev')

1 of XX START test not_null_stg_beneficiaries_beneficiary_key ............. [RUN]
2 of XX START test unique_stg_beneficiaries_beneficiary_key ............... [RUN]
...
XX of XX START test assert_disbursed_lte_committed ........................ [RUN]
XX of XX START test assert_payment_amount_positive ........................ [RUN]

Finished running XX tests in X.XXs.

Completed successfully

Done. PASS=XX WARN=0 ERROR=0 SKIP=0 TOTAL=XX
```

Key things to confirm:
- **PASS=XX, WARN=0, ERROR=0** — all tests pass with zero failures.
- The two singular tests (`assert_disbursed_lte_committed`, `assert_payment_amount_positive`) appear in the list and pass.

### Test coverage summary

The project includes the following test types:

| Test type | Models covered | Example |
|---|---|---|
| `not_null` | All primary key columns across all layers | `stg_beneficiaries.beneficiary_key` |
| `unique` | All primary key columns across all layers | `stg_payments.payment_id` |
| `accepted_values` | Status and category columns | `stg_payments.payment_status` → `['Success', 'Failed', 'Pending']` |
| Singular: `assert_disbursed_lte_committed` | `mart_donor_budget_vs_actual` | `total_disbursed` must not exceed `total_committed + 0.01` |
| Singular: `assert_payment_amount_positive` | `stg_payments` | `amount` must be strictly greater than 0 |

### Running tests for a specific model

```bash
dbt test --select stg_payments
dbt test --select mart_donor_budget_vs_actual
```

---

## Generating and Serving dbt Docs

### Generate the docs site

```bash
dbt docs generate
```

This compiles model SQL, reads all `schema.yml` descriptions, and writes static HTML/JSON artifacts to `dbt/target/`. Expected output:

```
Running with dbt=1.7.x
Found 16 models, ...

Catalog written to /path/to/dbt/target/catalog.json
```

### Serve the docs site locally

```bash
dbt docs serve
```

By default this starts a local HTTP server on port 8080:

```
Serving docs at 8080
To access from your browser, navigate to: http://localhost:8080
```

Open `http://localhost:8080` in your browser. Press `Ctrl+C` to stop the server.

To use a different port:

```bash
dbt docs serve --port 8888
```

### Navigating the docs site

**Model list (left sidebar):** All models are grouped by schema — `staging`, `intermediate`, `marts`. Click any model name to open its detail page showing the description, column list with types and descriptions, and the SQL definition.

**Lineage graph:** Click the network icon (bottom-right of any model page) or navigate to the "Lineage" tab to open the interactive DAG. The full lineage for this project flows:

```
sources (silver.*) → staging → intermediate → marts
```

Specifically:

```
silver.beneficiaries  ──► stg_beneficiaries ──► int_beneficiaries_payments ──► mart_payment_kpis
silver.payments       ──► stg_payments      ──┘                              └► mart_donor_budget_vs_actual
silver.donor_reports  ──► stg_donor_reports ──► int_donor_program_aggregates ──► mart_donor_budget_vs_actual
silver.afghan_refugees ─► stg_afghan_refugees ─► int_refugees_assistance ──► mart_refugee_assistance_summary
silver.refugee_assistance ► stg_refugee_assistance ──────────────────────┘
silver.refugee_protection ► stg_refugee_protection ──────────────────────────► mart_protection_caseload
```

Use the search box at the top of the lineage graph to highlight a specific model. Click any node to jump to its detail page. Use the `+` and `-` buttons to expand or collapse upstream/downstream nodes.

---

## Interpreting Test Failures

When `dbt test` reports failures, the output identifies the exact model, column, and test that failed. Here is how to read and debug each failure type.

### Reading the failure output

A failing test looks like:

```
Failure in test not_null_stg_payments_payment_id (models/staging/schema.yml)
  Got 42 results, configured to fail if != 0

  compiled Code at target/compiled/pspl/models/staging/schema.yml/not_null_stg_payments_payment_id.sql
```

The test name encodes the failure:
- `not_null_stg_payments_payment_id` → `not_null` test on `stg_payments.payment_id`
- `unique_int_beneficiaries_payments_beneficiary_key` → `unique` test on `int_beneficiaries_payments.beneficiary_key`
- `accepted_values_stg_payments_payment_status__Success__Failed__Pending` → `accepted_values` test on `stg_payments.payment_status`
- `assert_disbursed_lte_committed` → singular test in `dbt/tests/assert_disbursed_lte_committed.sql`

### Debugging a failing test

**Step 1 — Read the compiled SQL.** dbt writes the compiled test query to `target/compiled/`. Open the file path shown in the failure output:

```bash
cat target/compiled/pspl/models/staging/schema.yml/not_null_stg_payments_payment_id.sql
```

**Step 2 — Run the query directly against DuckDB** to inspect the failing rows:

```bash
duckdb pspl.duckdb < target/compiled/pspl/models/staging/schema.yml/not_null_stg_payments_payment_id.sql
```

Or open an interactive DuckDB session from the repo root:

```bash
duckdb pspl.duckdb
```

Then paste the compiled SQL to see the exact rows that caused the failure.

**Step 3 — Trace back to the source.** The compiled SQL references the model's view or table. Query the model directly to understand the data:

```sql
-- In the DuckDB interactive session:
SELECT * FROM staging.stg_payments WHERE payment_id IS NULL LIMIT 20;
SELECT * FROM staging.stg_payments WHERE amount <= 0 LIMIT 20;
```

**Step 4 — Identify the root cause.** Common causes:

| Failure | Likely cause | Fix |
|---|---|---|
| `not_null` on a primary key | Null values in the Silver source table | Check the Silver Delta table; re-run the PySpark notebook to clean the data |
| `unique` on a primary key | Duplicate rows survived deduplication | Inspect the Silver table for duplicates; add a `ROW_NUMBER()` dedup step in the staging model |
| `accepted_values` on a status column | New or misspelled value in the source | Add the new value to the `accepted_values` list in `schema.yml`, or clean it in staging |
| `assert_disbursed_lte_committed` | `total_disbursed > total_committed + 0.01` in `mart_donor_budget_vs_actual` | Check `stg_donor_reports` for data entry errors; the tolerance of 0.01 accounts for floating-point rounding |
| `assert_payment_amount_positive` | `amount <= 0` in `stg_payments` | Check the Silver `payments` table for zero or negative amounts; filter or correct them in the staging model |

**Step 5 — Re-run after fixing.** After correcting the data or model logic, re-run only the affected model and its tests:

```bash
dbt run --select stg_payments
dbt test --select stg_payments
```

---

## Adding a New Model

Follow the staging → intermediate → mart pattern used throughout the project. The steps below walk through adding a new mart that reports survey metric trends.

### Step 1 — Create the staging model (if the source is new)

If the source table does not already have a staging model, create one in `dbt/models/staging/`. Staging models must only rename columns, cast types, and handle nulls — no joins or aggregations.

```sql
-- dbt/models/staging/stg_surveys.sql  (already exists; shown as an example)
with source as (
    select * from {{ source('silver', 'surveys') }}
),
renamed as (
    select
        survey_id,
        beneficiary_id,
        NULLIF(metric_name, '')   as metric_name,
        NULLIF(district, '')      as district,
        NULLIF(program, '')       as program,
        CAST(survey_date AS DATE) as survey_date,
        CAST(metric_value AS INTEGER) as metric_value
    from source
)
select * from renamed
```

Add the model's columns and tests to `dbt/models/staging/schema.yml`.

### Step 2 — Create an intermediate model (if enrichment is needed)

Intermediate models join or enrich staging models. Place them in `dbt/models/intermediate/` and reference upstream models with `{{ ref() }}`.

```sql
-- dbt/models/intermediate/int_survey_trends.sql
with surveys as (
    select * from {{ ref('stg_surveys') }}
),
beneficiaries as (
    select beneficiary_key, district, program
    from {{ ref('stg_beneficiaries') }}
),
enriched as (
    select
        s.survey_id,
        s.metric_name,
        s.metric_value,
        s.survey_date,
        b.district,
        b.program
    from surveys s
    left join beneficiaries b
        on s.beneficiary_id = b.beneficiary_key
)
select * from enriched
```

Add descriptions and tests to `dbt/models/intermediate/schema.yml`.

### Step 3 — Create the mart model

Mart models produce aggregated, business-ready tables. Place them in `dbt/models/marts/`. They are materialized as tables (configured in `dbt_project.yml`).

```sql
-- dbt/models/marts/mart_survey_metric_trends.sql
with base as (
    select * from {{ ref('int_survey_trends') }}
),
monthly as (
    select
        metric_name,
        district,
        program,
        DATE_TRUNC('month', survey_date) as survey_month,
        AVG(metric_value)                as avg_metric_value,
        COUNT(*)                         as response_count
    from base
    group by metric_name, district, program, DATE_TRUNC('month', survey_date)
)
select * from monthly
```

### Step 4 — Add schema documentation

Add the new model to `dbt/models/marts/schema.yml` with a description for every column:

```yaml
- name: mart_survey_metric_trends
  description: >
    Monthly average survey metric values by metric name, district, and program.
  columns:
    - name: metric_name
      description: Name of the survey metric (e.g., food security, WASH).
      tests:
        - not_null
    - name: district
      description: Pakistani district where surveys were conducted.
      tests:
        - not_null
    - name: program
      description: Social protection program associated with the surveys.
      tests:
        - not_null
    - name: survey_month
      description: First day of the calendar month for which metrics are aggregated.
      tests:
        - not_null
    - name: avg_metric_value
      description: Average metric value across all survey responses in this segment and month.
      tests:
        - not_null
    - name: response_count
      description: Number of survey responses contributing to this aggregate.
      tests:
        - not_null
```

### Step 5 — Run and test the new model

```bash
# Build only the new model and its upstream dependencies
dbt run --select +mart_survey_metric_trends

# Test only the new model
dbt test --select mart_survey_metric_trends

# Regenerate docs to include the new model
dbt docs generate
```

### Layer responsibilities summary

| Layer | Directory | Materialization | Allowed operations |
|---|---|---|---|
| Staging | `models/staging/` | View | Column rename, type cast, `NULLIF` for empty strings |
| Intermediate | `models/intermediate/` | View | Joins between staging models, aggregations, enrichment |
| Mart | `models/marts/` | Table | Final aggregations, window functions, business KPIs |

Always use `{{ ref('model_name') }}` to reference other dbt models and `{{ source('silver', 'table_name') }}` to reference Silver Delta tables. Never hardcode table names in model SQL.

---

## Makefile Shortcuts

The repository `Makefile` includes targets for common dbt operations. Run these from the repository root:

```bash
make dbt-run      # equivalent to: cd dbt && dbt run
make dbt-test     # equivalent to: cd dbt && dbt test
make dbt-docs     # equivalent to: cd dbt && dbt docs generate && dbt docs serve
```
