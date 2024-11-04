
    
    

select
    survey_id as unique_field,
    count(*) as n_records

from "pspl"."main"."stg_surveys"
where survey_id is not null
group by survey_id
having count(*) > 1


