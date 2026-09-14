-- Independent expected population; EXCEPT ALL detects missing and duplicate days.
with expected as (
    select c.customer_id, cast(d.day as date) as date_day
    from {{ ref('stg_customers') }} as c,
    generate_series(date '{{ var("analysis_start") }}', date '{{ var("analysis_end") }}', interval 1 day) as d(day)
    where d.day >= c.signup_date
), actual as (
    select customer_id, date_day from {{ ref('fct_customer_daily') }}
)
(select * from expected except all select * from actual)
union all
(select * from actual except all select * from expected)
