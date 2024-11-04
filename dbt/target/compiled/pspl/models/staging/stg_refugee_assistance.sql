with source as (
    select * from delta_scan('C:/Users/Siddique/Desktop/Pakistani social protection landscape/delta_lake/silver/refugee_assistance')
),

transformed as (
    select
        assistance_id,
        refugee_id,
        program,
        modality,
        delivery_point,
        status,
        implementing_org,
        host_district,

        -- Type casts
        CAST(amount_usd AS DOUBLE)      as amount_usd,
        CAST(amount_pkr AS DOUBLE)      as amount_pkr,
        CAST(delivery_date AS DATE)     as delivery_date

    from source
)

select * from transformed