# Compatibility matrix

Result: **COMPATIBLE** (exit 0).

Measured in [hosted run 34906995612](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34906995612) at commit `8db49b54aab14bfcc848bfa5c5c0925bcb55a851`. This small generated report is retained intentionally; complete evidence is attached to the run. This is a lab compatibility result, not production approval.

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
| Image ID | sha256:99bcf404139543e15 | sha256:6cdcb589ba81b54c2 | Expected | Info |
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
| Materializations and selected config | same | same | Match | Critical |
| Relation names | same | same | Match | High |
| Selected manifest metadata | same | same | Match | High |
| Compiled SQL hashes (models and tests) | same | same | Match | High |
| Compiled SQL nodes checked | 52 | 52 | Info | Info |
| Model/test documentation | same | same | Match | High |
| seed node statuses and test failures | same | same | Match | Critical |
| seed node execution time sum (seconds) | 0.292 | 0.154 | Info | Info |
| build node statuses and test failures | same | same | Match | Critical |
| build node execution time sum (seconds) | 1.445 | 0.749 | Info | Info |
| test node statuses and test failures | same | same | Match | Critical |
| test node execution time sum (seconds) | 0.846 | 0.513 | Info | Info |
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

Full per-node timing and other informational details: `compatibility.json`.

## Evidence

- Baseline: `artifacts/ci/downloads/evidence-baseline/validation/result`
- Candidate: `artifacts/ci/downloads/evidence-candidate/validation/result`
