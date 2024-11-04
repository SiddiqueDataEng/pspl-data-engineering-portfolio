
    
    

select
    assistance_id as unique_field,
    count(*) as n_records

from "pspl"."main"."stg_refugee_assistance"
where assistance_id is not null
group by assistance_id
having count(*) > 1


