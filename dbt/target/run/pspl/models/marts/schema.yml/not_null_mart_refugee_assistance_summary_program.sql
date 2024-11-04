select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select program
from "pspl"."main"."mart_refugee_assistance_summary"
where program is null



      
    ) dbt_internal_test