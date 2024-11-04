select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select rolling_3m_avg_success_rate
from "pspl"."main"."mart_payment_kpis"
where rolling_3m_avg_success_rate is null



      
    ) dbt_internal_test