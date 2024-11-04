-- Protection Caseload KPI Query
-- Computes open caseload by incident type and risk level,
-- with a cumulative case count window function ordered by incident date.
-- Executable: duckdb pspl.duckdb < sql/protection_caseload.sql

WITH daily_cases AS (
    SELECT
        incident_type,
        risk_level,
        host_district,
        incident_date,
        SUM(CASE WHEN case_status != 'Closed' THEN 1 ELSE 0 END)   AS open_caseload,
        COUNT(*)                                                    AS case_count
    FROM main.stg_refugee_protection
    GROUP BY incident_type, risk_level, host_district, incident_date
),

with_cumulative AS (
    SELECT
        incident_type,
        risk_level,
        host_district,
        incident_date,
        open_caseload,
        case_count,
        SUM(case_count) OVER (
            PARTITION BY incident_type
            ORDER BY incident_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )                                                           AS cumulative_case_count
    FROM daily_cases
)

SELECT *
FROM with_cumulative
ORDER BY incident_type, incident_date, risk_level;
