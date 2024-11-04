select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select risk_level
from "pspl"."main"."mart_protection_caseload"
where risk_level is null



      
    ) dbt_internal_test