select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select reporting_month
from "pspl"."main"."mart_payment_kpis"
where reporting_month is null



      
    ) dbt_internal_test