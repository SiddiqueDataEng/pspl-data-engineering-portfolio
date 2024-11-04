select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select assistance_id
from "pspl"."main"."stg_refugee_assistance"
where assistance_id is null



      
    ) dbt_internal_test