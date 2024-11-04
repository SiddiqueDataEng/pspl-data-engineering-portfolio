with refugees as (
    select * from {{ ref('stg_afghan_refugees') }}
),

assistance as (
    select * from {{ ref('stg_refugee_assistance') }}
),

assistance_aggregates as (
    select
        refugee_id,
        SUM(amount_usd)             as total_assistance_usd,
        COUNT(*)                    as delivery_count,
        MAX(delivery_date)          as last_delivery_date
    from assistance
    group by refugee_id
),

joined as (
    select
        r.refugee_id,
        r.unhcr_case_number,
        r.name,
        r.gender,
        r.age,
        r.province_of_origin,
        r.arrival_wave,
        r.documentation_type,
        r.camp_settlement,
        r.host_district,
        r.family_size,
        r.vulnerability_score,
        r.is_unaccompanied_minor,
        r.has_disability,
        r.enrolled_in_program,
        r.return_intention,
        r.registration_date,
        r.last_verification,

        -- Assistance aggregates (null/0 when no assistance records exist)
        COALESCE(aa.total_assistance_usd, 0)    as total_assistance_usd,
        COALESCE(aa.delivery_count, 0)          as delivery_count,
        aa.last_delivery_date

    from refugees r
    left join assistance_aggregates aa
        on r.refugee_id = aa.refugee_id
)

select * from joined
