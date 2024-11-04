
    
    

select
    case_id as unique_field,
    count(*) as n_records

from "pspl"."main"."stg_refugee_protection"
where case_id is not null
group by case_id
having count(*) > 1


