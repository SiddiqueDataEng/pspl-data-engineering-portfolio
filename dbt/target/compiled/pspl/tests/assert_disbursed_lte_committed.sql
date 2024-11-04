-- Singular test: total_disbursed must not exceed total_committed by more than 0.01
-- (small tolerance for floating-point rounding).
-- This test passes when the query returns zero rows.

select
    donor,
    program,
    total_committed,
    total_disbursed
from "pspl"."main"."mart_donor_budget_vs_actual"
where total_disbursed > total_committed + 0.01