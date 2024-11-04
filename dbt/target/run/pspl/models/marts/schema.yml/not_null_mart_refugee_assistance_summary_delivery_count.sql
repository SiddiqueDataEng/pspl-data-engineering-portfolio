select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select delivery_count
from "pspl"."main"."mart_refugee_assistance_summary"
where delivery_count is null



      
    ) dbt_internal_test