select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select total_committed
from "pspl"."main"."mart_donor_budget_vs_actual"
where total_committed is null



      
    ) dbt_internal_test