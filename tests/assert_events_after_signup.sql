select e.*
from {{ ref('stg_product_events') }} as e
join {{ ref('stg_customers') }} as c using (customer_id)
where e.event_date < c.signup_date
