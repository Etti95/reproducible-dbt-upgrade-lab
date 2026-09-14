-- Strict casts fail on malformed inputs instead of turning invalid MRR into zero.
select
    subscription_id,
    customer_id,
    plan,
    cast(monthly_mrr as decimal(18, 2)) as monthly_mrr,
    status,
    cast(started_at as date) as started_at,
    cast(ended_at as date) as ended_at
from {{ ref('raw_subscriptions') }}
