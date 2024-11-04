select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select total_payments
from "pspl"."main"."int_beneficiaries_payments"
where total_payments is null



      
    ) dbt_internal_test