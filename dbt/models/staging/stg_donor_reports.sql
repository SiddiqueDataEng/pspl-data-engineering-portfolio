with source as (
    select * from {{ source('silver', 'donor_reports') }}
),

transformed as (
    select
        report_id,
        donor,
        program,
        reporting_period,
        currency,

        -- Type casts (cap disbursed at committed for synthetic rows where random draws violate the rule)
        CAST(amount_committed AS DOUBLE)    as amount_committed,
        LEAST(
            CAST(amount_disbursed AS DOUBLE),
            CAST(amount_committed AS DOUBLE)
        )                                     as amount_disbursed,
        CAST(disbursement_date AS DATE)     as disbursement_date

    from source
)

select * from transformed
