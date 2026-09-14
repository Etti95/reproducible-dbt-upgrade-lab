{% macro analysis_date_spine() %}
    {% if var('analysis_start') > var('analysis_end') %}
        {{ exceptions.raise_compiler_error('analysis_start must not exceed analysis_end') }}
    {% endif %}
    select cast(day as date) as date_day
    from generate_series(
        date '{{ var("analysis_start") }}',
        date '{{ var("analysis_end") }}',
        interval 1 day
    ) as dates(day)
{% endmacro %}
