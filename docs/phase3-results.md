# Phase 3 — Measured baseline validation

Local Docker run on September 14, 2026; not a GitHub Actions run.

Evidence: `artifacts/baseline/runs/20260914T173315790428Z/`.
Runtime: Python 3.12.11, dbt Core 1.10.11, dbt-duckdb 1.9.6, DuckDB 1.3.2, Linux/AMD64.

| Command | Measured result |
| --- | --- |
| deps | Exit 0; expected warning that no packages.yml packages exist |
| parse | Exit 0; parsed 6 models, 3 seeds, 46 data tests, 1 analysis |
| seed | Exit 0; loaded 8 customers, 10 subscription intervals, 13 events |
| build | Exit 0; 55 successful nodes: 6 models, 3 seeds, 46 tests; zero warnings/errors/skips in build summary |
| test | Exit 0; 46/46 passed |

There are 46 distinct data tests, not 92: the build and explicit test commands execute the same tests twice. Four models are views and two are tables. The reporting window is September 1–7, 2026.

## Inspected business output

| Customer | End-date USD MRR | Meaningful window events | Health |
| --- | ---: | ---: | --- |
| C001 | 100.00 | 3 | engaged |
| C002 | 300.00 | 2 | engaged |
| C003 | 0.00 | 1 | no_paid_subscription |
| C004 | 0.00 | 0 | no_paid_subscription |
| C005 | 150.00 | 2 | engaged |
| C006 | 70.00 | 1 | engaged |
| C007 | 0.00 | 0 | no_paid_subscription |
| C008 | 40.00 | 0 | needs_attention |

Total: eight customers and USD 660.00 MRR. This is contracted monthly run rate at September 7, not revenue earned during the seven-day window.

Direct read-only DuckDB inspection additionally confirmed 52 customer-days, 11 in-window events and nine meaningful events. The remaining two raw events are immediately outside the analysis window and remain visible in staging. MRR in the final mart is `DECIMAL(18,2)`. The inspection is retained locally at `artifacts/phase3-data-profile.json`.

## Artifact inspection

The post-build manifest contains:

```text
unique_id: model.reproducible_dbt_upgrade_lab.fct_customer_daily
materialized: table
relation_name: "lab"."analytics"."fct_customer_daily"
dependencies:
  stg_product_events
  int_customer_subscription_daily
  stg_customers
compiled_code: present
```

`build/target/run_results.json` contains 55 execution results. The separate `test/target/run_results.json` contains 46 test results, all `pass`. This is why preserving both invocations matters: the test-only file does not contain model build statuses.

## Initial failure and correction

The first attempt (`20260914T172823015242Z`) failed in `deps` because dbt tried to create `dbt_packages` under the read-only source mount. The project now routes the package installation path to `/evidence/dbt_packages`. The corrected run used a fresh evidence directory and passed. This is a filesystem/configuration correction, not an observed incompatibility between Core versions.

## What remains unproven

The candidate has not run this DAG yet. No artifact comparator or hosted CI workflow has executed. Passing baseline tests establishes the known-good lab behavior; it does not approve the candidate or prove that these rules fit an actual business's source data.
