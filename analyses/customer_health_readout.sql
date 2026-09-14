-- Direct DuckDB inspection after dbt build; intentionally executable without Jinja.
select customer_id, as_of_date, mrr_usd, active_subscription_count,
       meaningful_events_in_window, active_days_in_window, health_status
from analytics.mart_customer_health
order by customer_id;
