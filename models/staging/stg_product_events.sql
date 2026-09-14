select
    event_id,
    customer_id,
    cast(event_timestamp as timestamp) as event_timestamp,
    cast(event_timestamp as date) as event_date,
    event_type
from {{ ref('raw_product_events') }}
