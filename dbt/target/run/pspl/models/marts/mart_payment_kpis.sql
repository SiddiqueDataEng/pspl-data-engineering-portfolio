
  
    
    

    create  table
      "pspl"."main"."mart_payment_kpis__dbt_tmp"
  
    as (
      with payments as (
    select * from "pspl"."main"."stg_payments"
),

beneficiaries as (
    select
        beneficiary_key,
        district,
        program
    from "pspl"."main"."stg_beneficiaries"
),

payments_with_context as (
    select
        p.payment_id,
        p.payment_status,
        p.amount,
        p.payment_date,
        -- Truncate to first day of month for monthly aggregation
        DATE_TRUNC('month', p.payment_date)     as reporting_month,
        b.district,
        b.program
    from payments p
    left join beneficiaries b
        on p.beneficiary_id = b.beneficiary_key
),

monthly_aggregates as (
    select
        district,
        program,
        reporting_month,
        COUNT(*)                                                            as total_payments,
        SUM(CASE WHEN payment_status = 'Success' THEN 1 ELSE 0 END)        as successful_payments,
        SUM(CASE WHEN payment_status = 'Success' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0) * 1.0                                     as success_rate
    from payments_with_context
    group by district, program, reporting_month
),

with_rolling_avg as (
    select
        district,
        program,
        reporting_month,
        total_payments,
        successful_payments,
        success_rate,
        AVG(success_rate) OVER (
            PARTITION BY district, program
            ORDER BY reporting_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        )                                                                   as rolling_3m_avg_success_rate
    from monthly_aggregates
)

select * from with_rolling_avg
    );
  
  