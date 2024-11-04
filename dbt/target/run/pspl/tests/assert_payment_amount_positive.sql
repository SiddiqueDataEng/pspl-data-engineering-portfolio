select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      -- Singular test: every payment amount must be strictly positive (> 0).
-- This test passes when the query returns zero rows.

select
    payment_id,
    beneficiary_id,
    amount,
    payment_date
from "pspl"."main"."stg_payments"
where amount <= 0
      
    ) dbt_internal_test