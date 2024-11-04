select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select open_cases
from "pspl"."main"."mart_protection_caseload"
where open_cases is null



      
    ) dbt_internal_test