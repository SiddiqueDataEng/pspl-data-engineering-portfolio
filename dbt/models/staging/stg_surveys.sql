with source as (
    select * from {{ source('silver', 'surveys') }}
),

transformed as (
    select
        survey_id,
        beneficiary_id,
        metric_type                     as metric_name,
        field_worker                    as surveyor,
        district,
        program,

        -- Type casts
        CAST(survey_date AS DATE)       as survey_date,
        CAST(metric_value AS INTEGER)   as metric_value

    from source
)

select * from transformed
