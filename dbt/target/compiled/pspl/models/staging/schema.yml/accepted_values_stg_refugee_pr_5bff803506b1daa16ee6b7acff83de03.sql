
    
    

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


