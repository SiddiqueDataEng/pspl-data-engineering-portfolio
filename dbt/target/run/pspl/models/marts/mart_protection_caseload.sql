
  
    
    

    create  table
      "pspl"."main"."mart_protection_caseload__dbt_tmp"
  
    as (
      with protection as (
    select * from "pspl"."main"."stg_refugee_protection"
),

monthly_cases as (
    select
        incident_type,
        risk_level,
        host_district,
        DATE_TRUNC('month', incident_date)                                  as incident_month,
        SUM(CASE WHEN case_status != 'Closed' THEN 1 ELSE 0 END)           as open_cases,
        COUNT(*)                                                            as total_cases
    from protection
    group by incident_type, risk_level, host_district, DATE_TRUNC('month', incident_date)
),

with_cumulative as (
    select
        incident_type,
        risk_level,
        host_district,
        incident_month,
        open_cases,
        total_cases,
        SUM(total_cases) OVER (
            PARTITION BY incident_type
            ORDER BY incident_month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )                                                                   as cumulative_cases
    from monthly_cases
)

select * from with_cumulative
    );
  
  