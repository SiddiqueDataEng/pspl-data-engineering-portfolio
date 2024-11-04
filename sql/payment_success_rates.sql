-- Payment Success Rates KPI Query
-- Computes payment success rate per district and program per month,
-- with a 3-month rolling average using a window function.
-- Executable: duckdb pspl.duckdb < sql/payment_success_rates.sql

WITH payments_with_context AS (
    SELECT
        p.payment_id,
        p.payment_status,
        p.payment_date,
        DATE_TRUNC('month', p.payment_date)     AS month,
        b.district,
        b.program
    FROM main.stg_payments p
    LEFT JOIN main.stg_beneficiaries b
        ON p.beneficiary_id = b.beneficiary_key
),

monthly_rates AS (
    SELECT
        district,
        program,
        month,
        COUNT(*)                                                            AS total_payments,
        SUM(CASE WHEN payment_status = 'Success' THEN 1 ELSE 0 END)        AS successful_payments,
        SUM(CASE WHEN payment_status = 'Success' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0) * 1.0                                     AS success_rate
    FROM payments_with_context
    GROUP BY district, program, month
),

with_rolling_avg AS (
    SELECT
        district,
        program,
        month,
        total_payments,
        successful_payments,
        ROUND(success_rate, 4)                                              AS success_rate,
        ROUND(
            AVG(success_rate) OVER (
                PARTITION BY district, program
                ORDER BY month
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ),
            4
        )                                                                   AS rolling_3m_avg
    FROM monthly_rates
)

SELECT *
FROM with_rolling_avg
ORDER BY district, program, month;
