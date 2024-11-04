select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select cumulative_cases
from "pspl"."main"."mart_protection_caseload"
where cumulative_cases is null



      
    ) dbt_internal_test