select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select survey_id
from "pspl"."main"."stg_surveys"
where survey_id is null



      
    ) dbt_internal_test