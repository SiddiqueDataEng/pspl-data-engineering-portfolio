select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select total_disbursed
from "pspl"."main"."int_donor_program_aggregates"
where total_disbursed is null



      
    ) dbt_internal_test