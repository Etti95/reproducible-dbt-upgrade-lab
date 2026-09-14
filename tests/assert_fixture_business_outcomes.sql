{{ config(tags=['fixture_contract']) }}
-- Hand-calculated examples, intentionally scoped to the committed fixture/window.
-- Change these expectations only when intentionally changing the fixture contract.
with expected(customer_id, date_day, mrr_usd, active_subscription_count, event_count) as (
    values
      ('C001', date '2026-09-01', 100.00, 1, 2),
      ('C001', date '2026-09-07', 100.00, 1, 1),
      ('C002', date '2026-09-03', 200.00, 1, 1),
      ('C002', date '2026-09-04', 300.00, 1, 0),
      ('C003', date '2026-09-06', 80.00, 1, 1),
      ('C003', date '2026-09-07', 0.00, 0, 0),
      ('C004', date '2026-09-02', 0.00, 0, 1),
      ('C005', date '2026-09-02', 120.00, 1, 0),
      ('C005', date '2026-09-04', 150.00, 2, 2),
      ('C006', date '2026-09-02', 50.00, 1, 0),
      ('C006', date '2026-09-03', 0.00, 0, 0),
      ('C006', date '2026-09-06', 70.00, 1, 1),
      ('C007', date '2026-09-07', 0.00, 0, 1),
      ('C008', date '2026-09-05', 40.00, 1, 0)
)
select e.*, a.mrr_usd as actual_mrr
from expected as e left join {{ ref('fct_customer_daily') }} as a using (customer_id, date_day)
where e.mrr_usd is distinct from a.mrr_usd
    or e.active_subscription_count is distinct from a.active_subscription_count
    or e.event_count is distinct from a.event_count
