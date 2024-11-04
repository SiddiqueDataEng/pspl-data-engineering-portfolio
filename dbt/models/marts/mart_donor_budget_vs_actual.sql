with donor_aggregates as (
    select * from {{ ref('int_donor_program_aggregates') }}
),

with_variance_and_rank as (
    select
        donor,
        program,
        total_committed,
        total_disbursed,
        total_committed - total_disbursed                                   as variance,
        utilization_pct,
        RANK() OVER (
            PARTITION BY program
            ORDER BY utilization_pct DESC
        )                                                                   as utilization_rank
    from donor_aggregates
)

select * from with_variance_and_rank
