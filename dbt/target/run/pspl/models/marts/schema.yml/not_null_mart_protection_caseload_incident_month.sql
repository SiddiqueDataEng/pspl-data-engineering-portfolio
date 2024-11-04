select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select incident_month
from "pspl"."main"."mart_protection_caseload"
where incident_month is null



      
    ) dbt_internal_test