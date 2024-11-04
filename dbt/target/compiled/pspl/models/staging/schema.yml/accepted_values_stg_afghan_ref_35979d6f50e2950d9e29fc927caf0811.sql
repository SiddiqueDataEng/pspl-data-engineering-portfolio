
    
    

with all_values as (

    select
        return_intention as value_field,
        count(*) as n_records

    from "pspl"."main"."stg_afghan_refugees"
    group by return_intention

)

select *
from all_values
where value_field not in (
    'Yes','No','Undecided'
)


