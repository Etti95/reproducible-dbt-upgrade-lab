-- Expand source intervals independently; catch fanout introduced by the usage join.
with expected as (
    select cast(d.day as date) as date_day,
        cast(coalesce(sum(s.monthly_mrr), 0) as decimal(18,2)) as mrr_usd
    from generate_series(date '{{ var("analysis_start") }}', date '{{ var("analysis_end") }}', interval 1 day) as d(day)
    left join {{ ref('stg_subscriptions') }} as s
        on d.day >= s.started_at and (s.ended_at is null or d.day < s.ended_at)
    group by d.day
), actual as (
    select date_day, sum(mrr_usd) as mrr_usd
    from {{ ref('fct_customer_daily') }} group by date_day
)
select coalesce(e.date_day, a.date_day) as date_day, e.mrr_usd as expected, a.mrr_usd as actual
from expected as e full outer join actual as a using (date_day)
where e.mrr_usd is distinct from a.mrr_usd
