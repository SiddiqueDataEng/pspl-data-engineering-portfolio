-- Complaint Resolution KPI Query
-- Computes complaint volume, resolution rate, average resolution time,
-- and 90th percentile resolution time per district and category.
-- Executable: duckdb pspl.duckdb < sql/complaint_resolution.sql

WITH complaint_metrics AS (
    SELECT
        district,
        category,
        COUNT(*)                                                                AS total_complaints,
        SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END)                   AS resolved_complaints,
        SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0) * 1.0                                         AS resolution_rate,
        AVG(
            CASE
                WHEN status = 'Resolved' AND resolution_date IS NOT NULL
                THEN DATEDIFF('day', complaint_date, resolution_date)
            END
        )                                                                       AS avg_resolution_days,
        PERCENTILE_CONT(0.9) WITHIN GROUP (
            ORDER BY
                CASE
                    WHEN status = 'Resolved' AND resolution_date IS NOT NULL
                    THEN DATEDIFF('day', complaint_date, resolution_date)
                END
        )                                                                       AS p90_resolution_days
    FROM main.stg_complaints
    GROUP BY district, category
)

SELECT
    district,
    category,
    total_complaints,
    resolved_complaints,
    ROUND(resolution_rate, 4)           AS resolution_rate,
    ROUND(avg_resolution_days, 1)       AS avg_resolution_days,
    ROUND(p90_resolution_days, 1)       AS p90_resolution_days
FROM complaint_metrics
ORDER BY district, category;
