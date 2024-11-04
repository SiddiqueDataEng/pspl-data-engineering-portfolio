select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select total_cases
from "pspl"."main"."mart_protection_caseload"
where total_cases is null



      
    ) dbt_internal_test