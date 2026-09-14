select
    customer_id,
    cast(signup_date as date) as signup_date,
    country,
    segment
from {{ ref('raw_customers') }}
