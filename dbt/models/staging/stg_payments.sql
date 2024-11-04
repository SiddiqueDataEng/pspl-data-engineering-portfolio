with source as (
    select * from {{ source('silver', 'payments') }}
),

transformed as (
    select
        payment_id,
        beneficiary_id,
        payment_mode,
        payment_status,
        bank_code,
        transaction_ref,
        disbursement_center,

        -- Type casts
        CAST(amount AS BIGINT)          as amount,
        CAST(payment_date AS DATE)      as payment_date

    from source
)

select * from transformed
