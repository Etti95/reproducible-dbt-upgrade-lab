with dates as (
    {{ analysis_date_spine() }}
), customer_days as (
    select c.customer_id, d.date_day
    from {{ ref('stg_customers') }} as c
    cross join dates as d
    where d.date_day >= c.signup_date
)
select
    d.customer_id,
    d.date_day,
    count(s.subscription_id) as active_subscription_count,
    cast(coalesce(sum(s.monthly_mrr), 0) as decimal(18, 2)) as mrr_usd
from customer_days as d
left join {{ ref('stg_subscriptions') }} as s
    on d.customer_id = s.customer_id
    and d.date_day >= s.started_at
    and (s.ended_at is null or d.date_day < s.ended_at)
group by d.customer_id, d.date_day
