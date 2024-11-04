
  
  create view "pspl"."main"."stg_refugee_protection__dbt_tmp" as (
    with source as (
    select * from delta_scan('C:/Users/Siddique/Desktop/Pakistani social protection landscape/delta_lake/silver/refugee_protection')
),

transformed as (
    select
        case_id,
        refugee_id,
        incident_type,
        risk_level,
        case_status,
        reported_to,
        case_worker                     as assigned_officer,
        host_district,

        -- Type casts
        CAST(incident_date AS DATE)     as incident_date,
        CAST(follow_up_date AS DATE)    as follow_up_date

    from source
)

select * from transformed
  );
