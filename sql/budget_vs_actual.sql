-- Budget vs Actual KPI Query
-- Aggregates donor reports by donor and program, computes variance and utilization,
-- and ranks donors by utilization within each program.
-- Executable: duckdb pspl.duckdb < sql/budget_vs_actual.sql

WITH donor_program_totals AS (
    SELECT
        donor,
        program,
        SUM(amount_committed)                                           AS amount_committed,
        SUM(amount_disbursed)                                           AS amount_disbursed
    FROM main.stg_donor_reports
    GROUP BY donor, program
),

with_metrics AS (
    SELECT
        donor,
        program,
        amount_committed,
        amount_disbursed,
        amount_committed - amount_disbursed                             AS variance,
        amount_disbursed / NULLIF(amount_committed, 0) * 100           AS utilization_pct
    FROM donor_program_totals
),

with_rank AS (
    SELECT
        donor,
        program,
        amount_committed,
        amount_disbursed,
        variance,
        ROUND(utilization_pct, 2)                                       AS utilization_pct,
        RANK() OVER (
            PARTITION BY program
            ORDER BY utilization_pct DESC
        )                                                               AS donor_rank
    FROM with_metrics
)

SELECT *
FROM with_rank
ORDER BY program, donor_rank;
