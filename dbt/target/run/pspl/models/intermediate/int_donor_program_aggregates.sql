
  
  create view "pspl"."main"."int_donor_program_aggregates__dbt_tmp" as (
    with donor_reports as (
    select * from "pspl"."main"."stg_donor_reports"
),

aggregated as (
    select
        donor,
        program,
        SUM(amount_committed)                                               as total_committed,
        SUM(amount_disbursed)                                               as total_disbursed,
        SUM(amount_disbursed) / NULLIF(SUM(amount_committed), 0) * 100     as utilization_pct,
        COUNT(report_id)                                                    as report_count,
        MIN(disbursement_date)                                              as first_disbursement_date,
        MAX(disbursement_date)                                              as last_disbursement_date
    from donor_reports
    group by donor, program
)

select * from aggregated
  );
