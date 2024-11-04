select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

with all_values as (

    select
        risk_level as value_field,
        count(*) as n_records

    from "pspl"."main"."stg_refugee_protection"
    group by risk_level

)

select *
from all_values
where value_field not in (
    'Critical','High','Medium','Low'
)



      
    ) dbt_internal_test