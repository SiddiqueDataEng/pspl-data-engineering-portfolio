# Payment Success Rates — Sample Output

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
> duckdb pspl.duckdb < sql/payment_success_rates.sql
> ```

## Expected Output Schema

The query (`sql/payment_success_rates.sql`) produces one row per district × program × month
combination, with a 3-month rolling average success rate computed via a window function.

| Column | Type | Description |
|---|---|---|
| `district` | VARCHAR | Geographic district of the beneficiary |
| `program` | VARCHAR | Humanitarian programme name |
| `month` | DATE | First day of the calendar month (result of `DATE_TRUNC('month', payment_date)`) |
| `total_payments` | BIGINT | Total number of payment transactions in that district/programme/month |
| `successful_payments` | BIGINT | Number of transactions with `payment_status = 'Success'` |
| `success_rate` | DOUBLE | Fraction of successful payments: `successful_payments / total_payments`, rounded to 4 d.p. |
| `rolling_3m_avg` | DOUBLE | 3-month rolling average of `success_rate` (current month + 2 preceding months), partitioned by district and programme, rounded to 4 d.p. |

### Sample Rows (illustrative — not real data)

| district | program | month | total_payments | successful_payments | success_rate | rolling_3m_avg |
|---|---|---|---|---|---|---|
| Karachi | Cash Transfer | 2024-01-01 | 1200 | 1080 | 0.9000 | 0.9000 |
| Karachi | Cash Transfer | 2024-02-01 | 1350 | 1215 | 0.9000 | 0.9000 |
| Karachi | Cash Transfer | 2024-03-01 | 1100 | 935 | 0.8500 | 0.8833 |
| Lahore | Food Assistance | 2024-01-01 | 800 | 720 | 0.9000 | 0.9000 |

Results are ordered by `district`, `program`, then `month` ascending.
