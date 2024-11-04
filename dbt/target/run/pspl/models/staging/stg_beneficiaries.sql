
  
  create view "pspl"."main"."stg_beneficiaries__dbt_tmp" as (
    with source as (
    select * from delta_scan('C:/Users/Siddique/Desktop/Pakistani social protection landscape/delta_lake/silver/beneficiaries')
),

renamed as (
    select
        -- Primary key rename
        beneficiary_id                                  as beneficiary_key,

        -- String columns with null handling (replace empty strings with null)
        NULLIF(cnic, '')                                as cnic,
        NULLIF(name, '')                                as name,
        NULLIF(gender, '')                              as gender,
        NULLIF(phone, '')                               as phone,
        NULLIF(district, '')                            as district,
        NULLIF(tehsil, '')                              as tehsil,
        NULLIF(union_council, '')                       as union_council,
        NULLIF(program, '')                             as program,
        NULLIF(bank_account, '')                        as bank_account,

        -- Numeric columns
        age,
        family_size,

        -- Type casts
        CAST(registration_date AS DATE)                 as registration_date,
        CAST(last_payment_date AS DATE)                 as last_payment_date,
        CAST(poverty_score AS DOUBLE)                   as poverty_score,
        CAST(is_eligible AS BOOLEAN)                    as is_eligible,
        CAST(is_disabled AS BOOLEAN)                    as is_disabled

    from source
)

select * from renamed
  );
