select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    survey_id as unique_field,
    count(*) as n_records

from "pspl"."main"."stg_surveys"
where survey_id is not null
group by survey_id
having count(*) > 1



      
    ) dbt_internal_test