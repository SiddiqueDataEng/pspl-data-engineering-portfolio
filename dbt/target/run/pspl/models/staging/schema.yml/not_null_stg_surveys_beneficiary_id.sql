select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select beneficiary_id
from "pspl"."main"."stg_surveys"
where beneficiary_id is null



      
    ) dbt_internal_test