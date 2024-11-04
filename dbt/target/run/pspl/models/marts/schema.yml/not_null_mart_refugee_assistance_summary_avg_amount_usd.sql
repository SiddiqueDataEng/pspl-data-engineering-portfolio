select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select avg_amount_usd
from "pspl"."main"."mart_refugee_assistance_summary"
where avg_amount_usd is null



      
    ) dbt_internal_test