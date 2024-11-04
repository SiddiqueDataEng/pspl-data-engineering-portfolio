with beneficiaries as (
    select * from "pspl"."main"."stg_beneficiaries"
),

payments as (
    select * from "pspl"."main"."stg_payments"
),

payment_aggregates as (
    select
        beneficiary_id,
        COUNT(*)                    as total_payments,
        SUM(amount)                 as total_amount,
        MAX(payment_date)           as last_payment_date
    from payments
    group by beneficiary_id
),

joined as (
    select
        b.beneficiary_key,
        b.cnic,
        b.name,
        b.gender,
        b.age,
        b.district,
        b.tehsil,
        b.union_council,
        b.program,
        b.registration_date,
        b.poverty_score,
        b.family_size,
        b.is_disabled,
        b.is_eligible,
        b.bank_account,

        -- Payment aggregates (null when no payments exist)
        COALESCE(pa.total_payments, 0)      as total_payments,
        COALESCE(pa.total_amount, 0)        as total_amount,
        pa.last_payment_date

    from beneficiaries b
    left join payment_aggregates pa
        on b.beneficiary_key = pa.beneficiary_id
)

select * from joined