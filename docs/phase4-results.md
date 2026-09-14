# Phase 4 — Verified compatibility result

**COMPATIBLE under the current lab policy; exit code 0.** This is local Docker evidence, not hosted GitHub Actions or production approval.

Final run: `artifacts/comparisons/20260914T183847334897Z/`.

Tested Git revision: `a7b9f47379b7d8d745d81086ae027c9ad5cdfad3`, clean for both environments. Later documentation-only commits publish the result without changing the runtime-relevant source snapshot.

Source snapshot SHA-256: `0971bc450a3c67ad48aa396679eb9b6b6d010fe198fc0b04c7e10e02769c0d80`.

## Measured findings

- Baseline Core 1.10.11 and candidate Core 1.10.13 both passed deps, parse, seed, build and test.
- Both verified all 54 locked application packages plus the base-image pip. Only dbt-core changed version.
- Each build completed six models, three seeds and 46 tests, with zero failed/skipped nodes. The separate test command passed 46/46.
- All model/test compiled SQL hashes matched: 52 nodes.
- Node identities, dependencies, materializations, selected configuration, relation names and metadata matched.
- All nine seed/model exports matched in column names/types, row counts and exact typed contents: 174 rows across all exported relations.
- Both final marts contained eight customers and USD 660.00 of contracted MRR at September 7.
- Execution times differed; they are informational measurements from a small emulated-platform workload, not performance conclusions.
- All 21 comparator tests passed, including deliberately changed money with unchanged row count, missing artifacts, incorrect runtime inventory, and review-required SQL changes.

See the [retained matrix](compatibility_matrix.md) for the full readable comparison.

## Evidence paths

Under the final run directory:

```text
source/                         immutable-for-the-run source copy
baseline/source.json            file hashes and Git provenance
candidate/source.json           identical file hashes and Git provenance
{baseline,candidate}/environment/runtime.json
{baseline,candidate}/requirements.txt
{baseline,candidate}/commands.json
{baseline,candidate}/build/target/manifest.json
{baseline,candidate}/build/target/run_results.json
{baseline,candidate}/test/target/run_results.json
{baseline,candidate}/data.json
{baseline,candidate}/customer_health.csv
report/compatibility.json
report/compatibility.md
```

Full generated artifacts and DuckDB files stay out of Git. The small Markdown matrix is retained intentionally so a GitHub reader can inspect real example results. A fresh run reproduces the measurements with new run IDs/timings. CI upload/retention will be implemented in Phase 5.

## Investigation during implementation

The first paired run, `20260914T183547648125Z`, passed dbt in both environments but the comparator rejected evidence because it incorrectly required seed nodes to have `depends_on.nodes`. Real manifest v12 seeds use a macro-dependency structure. The reader now treats seed node-dependencies as empty while still requiring them on models/tests. A regression test covers missing model dependencies, and synthetic seed fixtures now use the observed structure.

Recomparison of the preserved first run passed after the fix. The final run above reran both environments from the corrected clean commit, so the published result does not depend solely on retroactively interpreting an older run.

## Engineering interpretation

This result supports compatibility for the tested project, fixtures, versions, platform and selected contracts. It does not show that a larger project, another adapter, incremental state, live warehouse permissions, or workload performance is unchanged. There was no observed transformation incompatibility between these two Core versions. Synthetic comparator tests are clearly separate from genuine dbt behavior.

Next: GitHub Actions jobs, retained hosted evidence, and a labeled failure/rollback drill. Production promotion still requires the migration and rollback process to be completed.
