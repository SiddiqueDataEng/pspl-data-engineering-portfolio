select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select total_assistance_usd
from "pspl"."main"."int_refugees_assistance"
where total_assistance_usd is null



      
    ) dbt_internal_test