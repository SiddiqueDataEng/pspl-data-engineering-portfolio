
    
    

select
    refugee_id as unique_field,
    count(*) as n_records

from "pspl"."main"."int_refugees_assistance"
where refugee_id is not null
group by refugee_id
having count(*) > 1


