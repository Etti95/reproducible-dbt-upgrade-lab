# Phase 4 — Compare behavior, not whole JSON files

## Objective and procedure

A successful build proves that the commands and tests executed in one environment. It does not prove that the same models were built, tests were preserved, SQL semantics stayed constant, or downstream column types and values stayed unchanged.

Run the experiment from the repository root after building both Phase 2 images:

```bash
python3 scripts/run_comparison.py
```

The runner freezes one copy of runtime-relevant source files, hashes each file, records Git provenance, and mounts that same copy read-only into two fresh containers. Runs execute sequentially locally to avoid competing for this laptop's resources. The candidate still runs if baseline validation fails, and comparison still produces a report. The Phase 5 workflow runs the same environment execution logic in independent hosted jobs.

Each environment runs inventory, deps, parse, seed, build, test, and a typed data export with networking disabled. Existing image tags are resolved to immutable local IDs before execution; the comparator checks each installed package against the source snapshot's lock and rejects extra packages in the full pip inventory. A stale image with a different lock fails instead of silently claiming the intended upgrade ran.

Expected evidence structure:

```text
artifacts/comparisons/<run-id>/
  source/                     frozen runtime-relevant files
  baseline/
    source.json               per-file hashes, aggregate hash, Git SHA and dirty flag
    requirements.txt          lock used to check image runtime
    policy.json               explicit expected runtime/counts/change policy
    completion.json           host-observed container exit
    image-inspect.json        actual image ID and platform
    environment/              installed runtime metadata and console inventories
    commands.json             exact executed commands and their exit codes
    <command>/target/         separate artifacts for parse/seed/build/test
    <command>/console.log
    validation.log
    data.json                 all seed/model schemas and typed rows
    customer_health.csv       readable business results
    lab.duckdb
  candidate/                  same evidence layout, isolated database
  report/
    compatibility.md          readable matrix and blocking differences
    compatibility.json        machine-readable decisions and details
```

The single-environment command remains available: `python3 scripts/run_project.py baseline`. Its new runs use `<run-id>/source/` and `<run-id>/result/`; older Phase 3 evidence retains its original layout.

## Inspect the source contract

`source.json` records all models, seeds, tests, macros, analyses, environment definitions, runner scripts, and runtime configuration. Documentation and generated output are excluded from the runtime hash. Git SHA and dirty status are separate facts: a snapshot can be content-addressed even when uncommitted, but this lab blocks promotion for review until the inputs have a clean committed reference. In CI, both jobs must check out the same SHA.

The source copy is checked before and after execution. Hashes are reproducibility evidence, not digital signatures or protection against an actor who can forge the whole evidence bundle. Production provenance should come from trusted CI and signed/attested artifacts.

## What the comparator reads

1. Validate completeness: expected commands, successful exits, inventory files, lock hashes, artifact schemas, runtime versions, source hashes, and full node coverage.
2. Check within-run consistency: command manifests describe the same graph; each execution artifact matches its manifest's invocation ID. Invocation IDs are used to detect mixed evidence, but not compared across environments.
3. Select stable graph properties: unique IDs, names, resource types, sorted dependencies, relation names, and materializations/configuration. Require the expected six models, three seeds, 46 tests, and one analysis.
4. Hash exact UTF-8 `compiled_code` for models and tests from the post-build manifest. Keep SQL bytes unchanged because whitespace can occur inside string literals. Textual changes require review, even if data matches this fixture.
5. Compare all execution IDs and statuses from seed/build/test artifacts. Missing results, skipped nodes, warnings, failures and duplicate result IDs cannot pass as successful coverage.
6. Compare exact relation schemas and row multisets for every seed/model. Capture per-node execution durations as information, not a noisy laptop performance gate.

The implemented compatibility policy is intentionally small and scoped to manifest v12 and run-results v6. It validates required fields for this lab, not every property in dbt's complete JSON schemas. Unknown schemas or unsupported source/metric resources require an explicit implementation change. It does not silently ignore a newly introduced external source.

The manifest describes project resources and their dependencies. Run results describe the nodes actually executed by one command. The files complement each other; a complete manifest is not proof that every listed node ran. See [manifest documentation](https://docs.getdbt.com/reference/artifacts/manifest-json) and [run results documentation](https://docs.getdbt.com/reference/artifacts/run-results-json).

## Stable fields and normalization

JSON object order and set-like dependency order do not matter. Row order does not matter, but duplicate rows do. Timestamps, worker thread names, absolute paths, and invocation IDs vary between runs and are not equality signals. Original artifacts remain intact for diagnosis.

Schema URIs are validated explicitly. dbt version differences are checked against declared environment versions, not removed blindly. Materialization, test severity/conditions, contract settings, hooks and other selected configuration remain part of the structural comparison. Documentation changes trigger review.

SQL hashing uses exact bytes rather than the preliminary Phase 1 trailing-whitespace normalization idea. This more conservative implementation avoids hiding whitespace changes inside SQL literals. Harmless formatting can require review; a false positive is preferable to silently declaring potentially changed SQL equivalent.

## Data export: beyond row counts

DuckDB `DESCRIBE` supplies exact types such as `DECIMAL(18,2)` rather than broad Python cursor type categories. Decimal values are encoded as decimal strings, dates/timestamps as explicitly tagged ISO strings, integers as integers, and null as JSON null. Unsupported types fail export until their representation is defined; no implicit float conversion loses monetary precision.

Rows are sorted by canonical JSON representation, with duplicates retained. Each relation includes its column order/types, row count, row content hash, and full rows. The comparator recomputes counts and hashes, compares values through hashes, and includes up to five differing row samples on failure. This is practical for a tiny lab; large production datasets need partitioned checksums, business aggregates, and targeted keyed comparisons.

## Decisions and exit codes

| Signal | Outcome | Exit behavior |
| --- | --- | --- |
| All required compatibility checks pass | Compatible under this policy | 0 |
| Expected Core version change; different image ID | Expected/informational | 0 |
| Execution time differences | Informational; inspect per-node timings | 0 |
| Compiled SQL or documentation differences | Human review; promotion blocked | 2 |
| Uncommitted/missing Git provenance | Human review; promotion blocked | 2 |
| Missing evidence, unsupported schema, failed command/test | Fail | 1 |
| Changed source, DAG, materialization, relation schema or data | Fail | 1 |
| Unexpected package changes or stale runtime lock | Fail | 1 |

Both nonzero codes block CI. Review is not an automatic waiver: investigate the exact node, check release notes and business outputs, then approve a narrowly scoped policy/expectation change through review and rerun. There is no blanket ignore-differences switch.

Recompare existing evidence without rerunning dbt:

```bash
python3 scripts/compare_artifacts.py \
  artifacts/comparisons/<run-id>/baseline \
  artifacts/comparisons/<run-id>/candidate \
  --policy artifacts/comparisons/<run-id>/source/environments/compatibility-policy.json \
  --output artifacts/comparisons/<run-id>/recheck
```

## Test the guardrail

```bash
python3 -m unittest discover -s scripts/tests -v
```

Synthetic artifacts test missing evidence, schema changes, materialization changes, equal-count monetary changes, failed/skipped coverage, mixed invocation IDs, lock drift, harmless timing/order differences, and review-required SQL changes. These are comparator tests, not claims that real dbt versions exhibited those regressions. Phase 5 also demonstrated labeled end-to-end rejection and baseline image recovery in hosted CI; see [the results](phase5-results.md).

There are 21 passing comparator tests. Manifest v12 seed dependencies are handled explicitly: seeds have macro dependencies but no required node-dependency list. Missing model/test dependencies still fail. This distinction was corrected after the first genuine artifact comparison rejected both runs; the originals and the failing report were preserved.

## Reasoning checkpoint

If both versions pass every SQL test but the candidate changes `mrr_usd` from `DECIMAL(18,2)` to `DOUBLE`, would you promote? The lab blocks it: small fixture values may look identical while downstream precision and interface guarantees change. Inspect the `Column names/types` row, not just the build summary.
