# Data Dictionary

This document defines every column in each of the four Gold-layer mart models produced by the dbt project. For each column the table lists the name, data type, description, and a representative example value.

---

## Table of Contents

- [mart\_payment\_kpis](#mart_payment_kpis)
- [mart\_donor\_budget\_vs\_actual](#mart_donor_budget_vs_actual)
- [mart\_refugee\_assistance\_summary](#mart_refugee_assistance_summary)
- [mart\_protection\_caseload](#mart_protection_caseload)

---

## mart\_payment\_kpis

Monthly payment KPI summary aggregated by district and program. Computes total and successful payment counts, success rate, and a 3-month rolling average success rate using a window function. Joins `stg_payments` with `stg_beneficiaries` to resolve district and program context.

**Source models**: `stg_payments`, `stg_beneficiaries`  
**Materialization**: table  
**Grain**: one row per district × program × calendar month

| Column | Data Type | Description | Example Value |
|---|---|---|---|
| `district` | VARCHAR | Pakistani district where the payments were made. Resolved by joining payments to beneficiaries on `beneficiary_id`. | `"Lahore"` |
| `program` | VARCHAR | Social protection program under which the payments were disbursed (e.g., cash transfer, food assistance). | `"Cash Transfer"` |
| `reporting_month` | DATE | First day of the calendar month for which these KPIs are computed. Derived via `DATE_TRUNC('month', payment_date)`. | `2024-01-01` |
| `total_payments` | BIGINT | Total number of payment transactions recorded for this district/program/month combination. | `342` |
| `successful_payments` | BIGINT | Number of payment transactions with `payment_status = 'Success'` in this district/program/month. | `298` |
| `success_rate` | DOUBLE | Ratio of successful payments to total payments, expressed as a decimal between 0.0 and 1.0. Calculated as `successful_payments / NULLIF(total_payments, 0)`. | `0.8713` |
| `rolling_3m_avg_success_rate` | DOUBLE | 3-month rolling average of `success_rate`, partitioned by district and program, ordered by `reporting_month`. Uses a window frame of `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`. | `0.8541` |

---

## mart\_donor\_budget\_vs\_actual

Budget vs actual disbursement summary by donor and program. Derived from `int_donor_program_aggregates`. Adds variance (committed minus disbursed) and a utilization rank within each program using a `RANK()` window function.

**Source models**: `int_donor_program_aggregates` → `stg_donor_reports`  
**Materialization**: table  
**Grain**: one row per donor × program

| Column | Data Type | Description | Example Value |
|---|---|---|---|
| `donor` | VARCHAR | Name of the donor organization that committed and disbursed funds. | `"UNHCR"` |
| `program` | VARCHAR | Name of the program funded by the donor. | `"Refugee Assistance"` |
| `total_committed` | DOUBLE | Sum of `amount_committed` (PKR) across all donor reports for this donor/program combination. | `5000000.0` |
| `total_disbursed` | DOUBLE | Sum of `amount_disbursed` (PKR) actually paid out for this donor/program combination. | `4250000.0` |
| `variance` | DOUBLE | Difference between committed and disbursed amounts (`total_committed - total_disbursed`). Positive values indicate underspend; negative values indicate overspend. | `750000.0` |
| `utilization_pct` | DOUBLE | Percentage of committed funds that have been disbursed, calculated as `total_disbursed / NULLIF(total_committed, 0) * 100`. Null when `total_committed` is zero. | `85.0` |
| `utilization_rank` | INTEGER | Rank of this donor within its program, ordered by `utilization_pct` descending. Rank 1 indicates the highest utilization within the program. Computed using the `RANK()` window function partitioned by `program`. | `1` |

---

## mart\_refugee\_assistance\_summary

Aggregated summary of refugee assistance delivery by program, modality, and host district. Joins `int_refugees_assistance` (for vulnerability scores) with `stg_refugee_assistance` (for transaction-level detail) to produce beneficiary counts, USD totals, and average vulnerability scores per delivery segment.

**Source models**: `int_refugees_assistance`, `stg_refugee_assistance`  
**Materialization**: table  
**Grain**: one row per program × modality × host district

| Column | Data Type | Description | Example Value |
|---|---|---|---|
| `program` | VARCHAR | Refugee assistance program under which deliveries were made (e.g., Emergency Cash, Winterization). | `"Emergency Cash"` |
| `modality` | VARCHAR | Delivery modality describing how assistance was provided (e.g., Cash Transfer, Food Voucher, In-Kind). | `"Cash Transfer"` |
| `host_district` | VARCHAR | Pakistani district where the assistance was delivered to refugees. | `"Peshawar"` |
| `total_beneficiaries` | BIGINT | Count of distinct refugees (`COUNT(DISTINCT refugee_id)`) who received assistance in this program/modality/district segment. | `1240` |
| `total_amount_usd` | DOUBLE | Total USD value of all assistance transactions delivered in this segment (`SUM(amount_usd)`). | `186000.0` |
| `avg_amount_usd` | DOUBLE | Average USD amount per delivery transaction in this segment. Calculated as `total_amount_usd / NULLIF(delivery_count, 0)`. | `150.0` |
| `delivery_count` | BIGINT | Total number of individual delivery transactions (`COUNT(*)`) recorded in this segment. | `1240` |
| `avg_vulnerability_score` | DOUBLE | Average vulnerability score (0–10 scale) of refugees who received assistance in this segment. Higher values indicate a more vulnerable population. Sourced from `int_refugees_assistance`. | `6.8` |

---

## mart\_protection\_caseload

Monthly protection caseload summary by incident type, risk level, and host district. Computes open and total case counts per month, plus a cumulative running total of cases partitioned by incident type using a window function.

**Source models**: `stg_refugee_protection`  
**Materialization**: table  
**Grain**: one row per incident type × risk level × host district × calendar month

| Column | Data Type | Description | Example Value |
|---|---|---|---|
| `incident_type` | VARCHAR | Type of protection incident recorded (e.g., GBV, Child Protection, Legal, SGBV). | `"GBV"` |
| `risk_level` | VARCHAR | Risk classification assigned to the incident (Critical, High, Medium, Low). | `"High"` |
| `host_district` | VARCHAR | Pakistani district where the protection incident occurred and was recorded. | `"Quetta"` |
| `incident_month` | DATE | First day of the calendar month in which the incidents occurred. Derived via `DATE_TRUNC('month', incident_date)`. | `2024-03-01` |
| `open_cases` | BIGINT | Number of cases with a status other than `'Closed'` in this segment and month. Calculated as `SUM(CASE WHEN case_status != 'Closed' THEN 1 ELSE 0 END)`. | `47` |
| `total_cases` | BIGINT | Total number of protection cases across all statuses in this segment and month (`COUNT(*)`). | `63` |
| `cumulative_cases` | BIGINT | Running total of `total_cases` partitioned by `incident_type`, ordered by `incident_month`. Uses a window frame of `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. Useful for tracking caseload growth over time. | `312` |
