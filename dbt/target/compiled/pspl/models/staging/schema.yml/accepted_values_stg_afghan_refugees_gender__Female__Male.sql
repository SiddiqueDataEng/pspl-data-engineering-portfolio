
    
    

with all_values as (

    select
        gender as value_field,
        count(*) as n_records

    from "pspl"."main"."stg_afghan_refugees"
    group by gender

)

select *
from all_values
where value_field not in (
    'Female','Male'
)


