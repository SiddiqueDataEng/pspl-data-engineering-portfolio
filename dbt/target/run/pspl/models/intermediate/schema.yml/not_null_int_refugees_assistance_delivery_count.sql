select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select delivery_count
from "pspl"."main"."int_refugees_assistance"
where delivery_count is null



      
    ) dbt_internal_test