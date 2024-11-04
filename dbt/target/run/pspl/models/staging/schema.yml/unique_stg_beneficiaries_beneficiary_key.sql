select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    beneficiary_key as unique_field,
    count(*) as n_records

from "pspl"."main"."stg_beneficiaries"
where beneficiary_key is not null
group by beneficiary_key
having count(*) > 1



      
    ) dbt_internal_test