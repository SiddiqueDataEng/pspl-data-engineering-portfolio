-- Singular test: every payment amount must be strictly positive (> 0).
-- This test passes when the query returns zero rows.

select
    payment_id,
    beneficiary_id,
    amount,
    payment_date
from {{ ref('stg_payments') }}
where amount <= 0
