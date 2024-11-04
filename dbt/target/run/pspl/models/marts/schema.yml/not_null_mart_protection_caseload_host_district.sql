select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select host_district
from "pspl"."main"."mart_protection_caseload"
where host_district is null



      
    ) dbt_internal_test