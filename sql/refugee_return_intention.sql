-- Refugee Return Intention KPI Query
-- Pivot-style aggregation of return intentions by province of origin and arrival wave,
-- with vulnerability score and intention breakdown percentages.
-- Executable: duckdb pspl.duckdb < sql/refugee_return_intention.sql

WITH intention_counts AS (
    SELECT
        province_of_origin,
        arrival_wave,
        ROUND(AVG(vulnerability_score), 4)                                  AS avg_vulnerability_score,
        COUNT(CASE WHEN return_intention = 'Yes' THEN 1 END)                AS intend_to_return,
        COUNT(CASE WHEN return_intention = 'Undecided' THEN 1 END)          AS undecided,
        COUNT(CASE WHEN return_intention = 'No' THEN 1 END)                 AS intend_to_stay,
        COUNT(*)                                                            AS total
    FROM main.stg_afghan_refugees
    GROUP BY province_of_origin, arrival_wave
),

with_pct AS (
    SELECT
        province_of_origin,
        arrival_wave,
        avg_vulnerability_score,
        intend_to_return,
        undecided,
        intend_to_stay,
        total,
        ROUND(
            intend_to_return / NULLIF(total, 0) * 100.0,
            2
        )                                                                   AS return_intention_pct
    FROM intention_counts
)

SELECT *
FROM with_pct
ORDER BY province_of_origin, arrival_wave;
