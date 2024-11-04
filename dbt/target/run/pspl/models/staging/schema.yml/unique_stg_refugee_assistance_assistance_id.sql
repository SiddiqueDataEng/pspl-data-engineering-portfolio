select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    assistance_id as unique_field,
    count(*) as n_records

from "pspl"."main"."stg_refugee_assistance"
where assistance_id is not null
group by assistance_id
having count(*) > 1



      
    ) dbt_internal_test