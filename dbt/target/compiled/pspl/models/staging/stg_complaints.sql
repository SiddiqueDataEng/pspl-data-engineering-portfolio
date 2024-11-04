with source as (
    select * from delta_scan('C:/Users/Siddique/Desktop/Pakistani social protection landscape/delta_lake/silver/complaints')
),

transformed as (
    select
        complaint_id,
        cnic,
        category,
        description,
        status,
        assigned_to,
        district,

        -- Type casts
        CAST(complaint_date AS DATE)    as complaint_date,
        CAST(resolution_date AS DATE)   as resolution_date

    from source
)

select * from transformed