select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select beneficiary_key
from "pspl"."main"."stg_beneficiaries"
where beneficiary_key is null



      
    ) dbt_internal_test