with usage_daily as (
    select
        customer_id,
        event_date,
        count(*) as event_count,
        sum(case when event_type in ('project_created', 'report_exported') then 1 else 0 end) as meaningful_event_count
    from {{ ref('stg_product_events') }}
    group by customer_id, event_date
)
select
    s.customer_id,
    s.date_day,
    c.country,
    c.segment,
    s.active_subscription_count,
    s.mrr_usd,
    coalesce(u.event_count, 0) as event_count,
    coalesce(u.meaningful_event_count, 0) as meaningful_event_count
from {{ ref('int_customer_subscription_daily') }} as s
inner join {{ ref('stg_customers') }} as c on s.customer_id = c.customer_id
left join usage_daily as u on s.customer_id = u.customer_id and s.date_day = u.event_date
