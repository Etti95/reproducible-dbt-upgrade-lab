-- Staging must not silently filter or deduplicate the raw fixture.
{% for raw, stage in [('raw_customers', 'stg_customers'), ('raw_subscriptions', 'stg_subscriptions'), ('raw_product_events', 'stg_product_events')] %}
select '{{ stage }}' as model_name
where (select count(*) from {{ ref(raw) }}) != (select count(*) from {{ ref(stage) }})
{% if not loop.last %}union all{% endif %}
{% endfor %}
