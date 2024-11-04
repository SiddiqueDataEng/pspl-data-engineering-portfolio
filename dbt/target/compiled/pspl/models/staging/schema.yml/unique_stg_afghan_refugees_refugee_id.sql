
    
    

select
    refugee_id as unique_field,
    count(*) as n_records

from "pspl"."main"."stg_afghan_refugees"
where refugee_id is not null
group by refugee_id
having count(*) > 1


