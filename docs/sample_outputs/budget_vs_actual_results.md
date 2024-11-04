# Budget vs Actual — Sample Output

> **Note:** This file is a placeholder. The DuckDB database (`pspl.duckdb`) has not been
> generated yet because the full pipeline has not been run.
>
> To generate the database and populate this file with real results, run the pipeline first:
>
> ```bash
> # Option 1 — run everything via Make
> make all
>
> # Option 2 — run each step manually
> python ingest/ingest.py
> jupyter nbconvert --to notebook --execute notebooks/delta_lake_operations.ipynb
> cd dbt && dbt run
> ```
>
> Once `pspl.duckdb` exists, execute the query and capture the output:
>
> ```bash
> duckdb pspl.duckdb < sql/budget_vs_actual.sql
> ```

## Expected Output Schema

The query (`sql/budget_vs_actual.sql`) produces one row per donor × program combination,
ranked by utilisation within each program.

| Column | Type | Description |
|---|---|---|
| `donor` | VARCHAR | Donor organisation name |
| `program` | VARCHAR | Humanitarian programme name |
| `amount_committed` | DOUBLE | Total amount committed by the donor for the programme (PKR) |
| `amount_disbursed` | DOUBLE | Total amount actually disbursed (PKR) |
| `variance` | DOUBLE | Undisbursed balance: `amount_committed − amount_disbursed` |
| `utilization_pct` | DOUBLE | Percentage of committed funds disbursed: `(amount_disbursed / amount_committed) × 100`, rounded to 2 d.p. |
| `donor_rank` | BIGINT | Rank of the donor within the programme, ordered by `utilization_pct` descending (1 = highest utilisation) |

### Sample Rows (illustrative — not real data)

| donor | program | amount_committed | amount_disbursed | variance | utilization_pct | donor_rank |
|---|---|---|---|---|---|---|
| UNHCR | Cash Transfer | 5000000.00 | 4750000.00 | 250000.00 | 95.00 | 1 |
| UNICEF | Cash Transfer | 3000000.00 | 2400000.00 | 600000.00 | 80.00 | 2 |
| WFP | Food Assistance | 8000000.00 | 7200000.00 | 800000.00 | 90.00 | 1 |

Results are ordered by `program`, then `donor_rank` ascending.
