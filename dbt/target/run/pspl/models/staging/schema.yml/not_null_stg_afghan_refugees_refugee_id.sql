select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select refugee_id
from "pspl"."main"."stg_afghan_refugees"
where refugee_id is null



      
    ) dbt_internal_test