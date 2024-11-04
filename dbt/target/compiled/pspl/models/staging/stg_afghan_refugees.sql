with source as (
    select * from delta_scan('C:/Users/Siddique/Desktop/Pakistani social protection landscape/delta_lake/silver/afghan_refugees')
),

transformed as (
    select
        refugee_id,
        unhcr_case_number,
        name,
        gender,
        age,
        province_of_origin,
        arrival_wave,
        documentation_type,
        camp_settlement,
        host_district,
        family_size,
        is_unaccompanied_minor,
        has_disability,
        enrolled_in_program,
        return_intention,

        -- Type casts
        CAST(registration_date AS DATE)     as registration_date,
        CAST(last_verification AS DATE)     as last_verification,
        CAST(vulnerability_score AS DOUBLE) as vulnerability_score

    from source
)

select * from transformed