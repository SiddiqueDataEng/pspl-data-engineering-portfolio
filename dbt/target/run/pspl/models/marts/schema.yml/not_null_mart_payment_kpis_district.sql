select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select district
from "pspl"."main"."mart_payment_kpis"
where district is null



      
    ) dbt_internal_test