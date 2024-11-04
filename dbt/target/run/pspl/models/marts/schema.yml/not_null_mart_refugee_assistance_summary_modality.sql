select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select modality
from "pspl"."main"."mart_refugee_assistance_summary"
where modality is null



      
    ) dbt_internal_test