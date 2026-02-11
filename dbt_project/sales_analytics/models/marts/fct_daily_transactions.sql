-- Daily transaction summary
-- Aggregates transaction metrics by day

{{
    config(
        materialized='table'
    )
}}

with transactions as (
    select * from {{ ref('stg_transactions') }}
),

dates as (
    select * from {{ source('bfsi', 'dim_date') }}
),

daily_summary as (
    select
        d.date,
        d.year,
        d.quarter,
        d.month,
        d.month_name,
        count(distinct t.transaction_key) as transaction_count,
        sum(t.transaction_amount) as total_amount,
        avg(t.transaction_amount) as avg_amount,
        sum(t.transaction_fee) as total_fees
    from transactions t
    join dates d on t.date_key = d.date_key
    group by
        d.date,
        d.year,
        d.quarter,
        d.month,
        d.month_name
)

select * from daily_summary
