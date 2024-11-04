select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select successful_payments
from "pspl"."main"."mart_payment_kpis"
where successful_payments is null



      
    ) dbt_internal_test