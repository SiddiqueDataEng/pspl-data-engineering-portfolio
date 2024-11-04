select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select utilization_rank
from "pspl"."main"."mart_donor_budget_vs_actual"
where utilization_rank is null



      
    ) dbt_internal_test