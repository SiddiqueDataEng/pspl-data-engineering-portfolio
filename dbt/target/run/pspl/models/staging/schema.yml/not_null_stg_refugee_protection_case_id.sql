select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select case_id
from "pspl"."main"."stg_refugee_protection"
where case_id is null



      
    ) dbt_internal_test