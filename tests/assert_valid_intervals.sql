select s.*
from {{ ref('stg_subscriptions') }} as s
left join {{ ref('stg_customers') }} as c using (customer_id)
where s.started_at is null
    or (s.ended_at is not null and s.ended_at <= s.started_at)
    or s.started_at < c.signup_date
    or (s.status = 'cancelled' and s.ended_at is null)
