
  
    
    

    create  table
      "pspl"."main"."mart_refugee_assistance_summary__dbt_tmp"
  
    as (
      with refugees_assistance as (
    select * from "pspl"."main"."int_refugees_assistance"
),

assistance as (
    select * from "pspl"."main"."stg_refugee_assistance"
),

-- Join assistance transactions with refugee vulnerability scores
assistance_with_vulnerability as (
    select
        a.assistance_id,
        a.refugee_id,
        a.program,
        a.modality,
        a.host_district,
        a.amount_usd,
        a.delivery_date,
        ra.vulnerability_score
    from assistance a
    left join refugees_assistance ra
        on a.refugee_id = ra.refugee_id
),

aggregated as (
    select
        program,
        modality,
        host_district,
        COUNT(DISTINCT refugee_id)          as total_beneficiaries,
        SUM(amount_usd)                     as total_amount_usd,
        SUM(amount_usd)
            / NULLIF(COUNT(*), 0)           as avg_amount_usd,
        COUNT(*)                            as delivery_count,
        AVG(vulnerability_score)            as avg_vulnerability_score
    from assistance_with_vulnerability
    group by program, modality, host_district
)

select * from aggregated
    );
  
  