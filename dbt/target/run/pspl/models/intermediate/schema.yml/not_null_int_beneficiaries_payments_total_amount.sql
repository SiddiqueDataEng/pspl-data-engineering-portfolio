select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select total_amount
from "pspl"."main"."int_beneficiaries_payments"
where total_amount is null



      
    ) dbt_internal_test