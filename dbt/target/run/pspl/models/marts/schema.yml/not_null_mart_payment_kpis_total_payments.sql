select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select total_payments
from "pspl"."main"."mart_payment_kpis"
where total_payments is null



      
    ) dbt_internal_test