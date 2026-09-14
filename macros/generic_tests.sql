{% test nonnegative(model, column_name) %}
select * from {{ model }}
where {{ column_name }} is null or {{ column_name }} < 0
{% endtest %}

{% test unique_customer_day(model) %}
select customer_id, date_day, count(*) as row_count
from {{ model }}
group by customer_id, date_day
having count(*) != 1 or customer_id is null or date_day is null
{% endtest %}
