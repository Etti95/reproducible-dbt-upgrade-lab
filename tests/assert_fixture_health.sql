{{ config(tags=['fixture_contract']) }}
with expected(customer_id, mrr_usd, meaningful_events_in_window, active_days_in_window, health_status) as (
    values
      ('C001', 100.00, 3, 2, 'engaged'),
      ('C002', 300.00, 2, 2, 'engaged'),
      ('C003', 0.00, 1, 1, 'no_paid_subscription'),
      ('C004', 0.00, 0, 0, 'no_paid_subscription'),
      ('C005', 150.00, 2, 1, 'engaged'),
      ('C006', 70.00, 1, 1, 'engaged'),
      ('C007', 0.00, 0, 0, 'no_paid_subscription'),
      ('C008', 40.00, 0, 0, 'needs_attention')
), actual as (
    select customer_id, mrr_usd, meaningful_events_in_window, active_days_in_window, health_status
    from {{ ref('mart_customer_health') }}
)
(select * from expected except all select * from actual)
union all
(select * from actual except all select * from expected)
