{{ config(tags=['customer_success']) }}

with usage_window as (
    select
        customer_id,
        sum(meaningful_event_count) as meaningful_events_in_window,
        count(case when meaningful_event_count > 0 then 1 end) as active_days_in_window
    from {{ ref('fct_customer_daily') }}
    group by customer_id
)
select
    d.customer_id,
    d.date_day as as_of_date,
    d.country,
    d.segment,
    d.mrr_usd,
    d.active_subscription_count,
    u.meaningful_events_in_window,
    u.active_days_in_window,
    case
        when d.mrr_usd = 0 then 'no_paid_subscription'
        when u.meaningful_events_in_window = 0 then 'needs_attention'
        else 'engaged'
    end as health_status
from {{ ref('fct_customer_daily') }} as d
inner join usage_window as u on d.customer_id = u.customer_id
where d.date_day = date '{{ var("analysis_end") }}'
