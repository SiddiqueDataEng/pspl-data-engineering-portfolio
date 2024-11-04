select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select success_rate
from "pspl"."main"."mart_payment_kpis"
where success_rate is null



      
    ) dbt_internal_test