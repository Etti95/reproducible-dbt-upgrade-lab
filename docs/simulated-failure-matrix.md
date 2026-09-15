# SIMULATED FAILURE — compatibility matrix

Result: **FAIL** (exit 1).

Intentional failure from [hosted run 34930708294](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34930708294), dispatched with `simulate_failure=true` at commit `8db49b54aab14bfcc848bfa5c5c0925bcb55a851`. Both environments passed dbt. This is a fabricated artifact mutation, not an observed dbt regression.

| Check | Baseline | Candidate | Result | Severity |
| --- | --- | --- | --- | --- |
| Evidence completeness and internal consistency | Pass | Pass | Compatible | Critical |
| Source file hashes | same | same | Match | Critical |
| Source snapshot hash | same | same | Match | Critical |
| Git revision | same | same | Match | Critical |
| Python | 3.12.11 | 3.12.11 | Match | Info |
| Platform | x86_64 | x86_64 | Match | Info |
| dbt-duckdb | 1.9.6 | 1.9.6 | Match | Info |
| duckdb | 1.3.2 | 1.3.2 | Match | Info |
| Package: dbt-core | 1.10.11 | 1.10.13 | Expected | Info |
| Locked package count | 54 | 54 | Info | Info |
| Image ID | sha256:9d9913d90eb39f647 | sha256:61be0effca63da904 | Expected | Info |
| dbt deps | Pass | Pass | Compatible | Critical |
| dbt parse | Pass | Pass | Compatible | Critical |
| dbt seed | Pass | Pass | Compatible | Critical |
| dbt build | Pass | Pass | Compatible | Critical |
| dbt test | Pass | Pass | Compatible | Critical |
| model node count | 6 | 6 | Match | High |
| seed node count | 3 | 3 | Match | High |
| test node count | 46 | 46 | Match | High |
| analysis node count | 1 | 1 | Match | High |
| Node IDs | same | same | Match | Critical |
| Node names | same | same | Match | High |
| Resource types | same | same | Match | Critical |
| DAG dependencies | same | same | Match | High |
| Materializations and selected config | differs | differs | Fail | Critical |
| Relation names | same | same | Match | High |
| Selected manifest metadata | same | same | Match | High |
| Compiled SQL hashes (models and tests) | same | same | Match | High |
| Compiled SQL nodes checked | 52 | 52 | Info | Info |
| Model/test documentation | same | same | Match | High |
| seed node statuses and test failures | same | same | Match | Critical |
| seed node execution time sum (seconds) | 0.165 | 0.154 | Info | Info |
| build node statuses and test failures | same | same | Match | Critical |
| build node execution time sum (seconds) | 1.113 | 0.872 | Info | Info |
| test node statuses and test failures | same | same | Match | Critical |
| test node execution time sum (seconds) | 0.661 | 0.512 | Info | Info |
| Distinct tests passing | 46/46 | 46/46 | Compatible | Critical |
| Column names/types | same | same | Match | High |
| Row counts | same | same | Match | High |
| Typed data contents | same | same | Match | High |
| Rows: fct_customer_daily | 52 | 52 | Match | High |
| Rows: int_customer_subscription_daily | 52 | 52 | Match | High |
| Rows: mart_customer_health | 8 | 8 | Match | High |
| Rows: stg_customers | 8 | 8 | Match | High |
| Rows: stg_product_events | 13 | 13 | Match | High |
| Rows: stg_subscriptions | 10 | 10 | Match | High |
| Rows: raw_customers | 8 | 8 | Match | High |
| Rows: raw_product_events | 13 | 13 | Match | High |
| Rows: raw_subscriptions | 10 | 10 | Match | High |

## Materializations and selected config

```json
[
  {
    "id": "model.reproducible_dbt_upgrade_lab.mart_customer_health",
    "baseline": {
      "materialized": "table",
      "enabled": true,
      "unique_key": null,
      "incremental_strategy": null,
      "on_schema_change": "ignore",
      "contract": {
        "enforced": false,
        "alias_types": true
      },
      "pre-hook": [],
      "post-hook": [],
      "grants": {},
      "column_types": {}
    },
    "candidate": {
      "materialized": "view",
      "enabled": true,
      "unique_key": null,
      "incremental_strategy": null,
      "on_schema_change": "ignore",
      "contract": {
        "enforced": false,
        "alias_types": true
      },
      "pre-hook": [],
      "post-hook": [],
      "grants": {},
      "column_types": {}
    }
  }
]
```

Full per-node timing and other informational details: `compatibility.json`.

## Evidence

- Baseline: `artifacts/ci/downloads/evidence-baseline/validation/result`
- Candidate: `artifacts/ci/candidate-simulated`
