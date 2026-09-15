# Engineering retrospective

## What could have happened without these controls?

An unchanged deployment commit could have been rebuilt with another CLI, adapter, transitive dependency or base image. The job might fail at startup, interpret configuration differently, or execute successfully while changing a downstream contract. Teams might first discover the problem through late dashboards or incorrect customer/revenue reporting.

The lab does not claim that this actually happened to a production customer. It demonstrates the failure mechanism and the controls that make a dependency change explicit and reviewable. The genuine pip-tools/pip incompatibility found during development illustrates that even a successful installation does not prove a tool can perform its job.

## Which control provides the most protection?

For the incident's specific risk of silent runtime replacement, the strongest operational protection is deploying and retaining an approved immutable image instead of resolving dependencies during deployment. The hashed transitive lock and base digest control how that image is built; the retained image avoids rebuild/download uncertainty during rollback.

That does not prove the image is correct. The most important acceptance gate is the combination of complete execution evidence, semantic artifact comparison, typed data comparison and independently specified business tests. Reproducibility prevents unplanned input drift; compatibility testing evaluates planned changes; correctness checks assert business meaning.

## What does Docker solve, and what does it not solve?

Docker packages the interpreter, CLI, adapter and dependencies in an isolated runtime and makes the tested image transferable. In this lab, baseline and candidate run separately, and a fresh CI runner recovered the retained baseline image without rebuilding it.

A Dockerfile is still a build recipe. Mutable tags, unpinned package installs, remote scripts and external downloads can change its output. Even controlled builds can have different image IDs because build metadata varies. The host kernel, daemon, CPU architecture, source data, permissions and external services also affect behavior. The lab fixes a Linux/AMD64 userspace runtime; it does not claim bit-identical hosted VMs or universally portable performance.

## Why isn't passing dbt build alone enough?

A build passes the tests that actually ran, on the inputs provided. It can still omit expected nodes, preserve row counts while changing values, change column precision/materialization, or exercise too little data to reveal changed SQL semantics. A manifest describes the graph; run results establish execution coverage. Both are needed.

Our genuine upgrade passed 46 tests in each environment, matched all 52 compiled model/test SQL hashes, and matched the schemas and typed values of all nine exported relations. The simulated `mart_customer_health` table-to-view mutation was rejected even though the retained SQL/data results remained successful. That simulation proves the gate, not an actual regression in Core 1.10.13.

## What would change for BigQuery or Snowflake?

Keep the same experiment design, but replace DuckDB-specific assumptions with actual warehouse guarantees:

- Use the appropriate pinned adapter and short-lived workload credentials; validate actual role/grant, schema and network behavior. Keep secrets and sensitive data out of public artifact bundles.
- Run against isolated datasets/schemas and controlled input snapshots. Compare relation names with an explicit mapping for the intended environment namespace while preserving schema/object identity; do not erase meaningful differences broadly.
- Test incremental merges, late arrivals, deletions, schema changes, retries and backfills. Prove equivalence between an incremental path and the intended full-refresh result where applicable.
- Compare partitioned counts/checksums and business aggregates, with targeted keyed diffs. Define exact monetary representations and explicit tolerances only where approximate numeric types require them.
- Track warehouse-native query IDs, duration, bytes/credits, concurrency, freshness and downstream BI consumption. Set thresholds from representative workloads; this lab's tiny fixture timings are not a production benchmark.
- Retain both runtime images and a separate data restoration mechanism. BigQuery table snapshots and Snowflake Time Travel/cloning can support controlled inputs or recovery, subject to each platform's object and retention rules. Validate the actual scope and restore procedure before a release. See [BigQuery snapshots](https://docs.cloud.google.com/bigquery/docs/table-snapshots-intro) and [Snowflake Time Travel](https://docs.snowflake.com/en/user-guide/data-time-travel).

These are production extensions, not capabilities this DuckDB repository pretends to have implemented.

## How would this change for 500 models and multiple teams?

Assign owners to model domains and shared interfaces, agree criticality/acceptance criteria, and inventory macros, packages, Python models and adapter-specific features before choosing upgrade waves. Publish one reviewed runtime/lock policy rather than letting each team resolve its own dependency set in CI.

Use fast parse/configuration and contract checks on every change. Use selective builds for ordinary code changes, plus representative domain suites and scheduled full integration runs. A dependency-only upgrade can affect unchanged models across the graph: do not assume `state:modified+` provides full upgrade coverage merely because SQL files were untouched. dbt state selection compares project attributes against prior artifacts; those artifacts themselves have version and comparison caveats. See [state selection](https://docs.getdbt.com/reference/node-selection/methods#state) and [state comparison caveats](https://docs.getdbt.com/reference/node-selection/state-comparison-caveats).

Partition data comparisons, retain immutable reference manifests separately from current output paths, and require expected coverage for every selected test suite. Route differences to domain owners, with time-bounded, node-specific exceptions rather than a growing global ignore list. Benchmark realistic warehouse concurrency and cost before promotion.

Roll out by domain or workload with a central release owner and clear dependency ordering. Keep only one writer for each production relation during cutover. Rehearse restoration, retain prior image and data references, and run a full representative integration gate before broad adoption. Complexity should come from demonstrated scale and risk, not from adding tools to a six-model lab.

## What this implementation taught us

The first compiler toolchain installed but failed during hash generation, so we tested and locked the compatible compiler/pip pair. The first artifact reader mishandled the seed-specific dependency structure, so we corrected it and added a regression case rather than silently defaulting all missing dependencies to empty. A read-only source mount exposed dbt's package-directory write, which we redirected to the run's evidence volume.

These were different kinds of failures: toolchain compatibility, evidence-reader correctness, and execution configuration. Distinguishing them prevents a misleading claim that every problem was a dbt Core regression. Both genuine Core environments passed the finished lab.

## TL;DR

**Problem →** The same Git commit can run with a different dbt environment after dependencies or image tags change.

**Risk →** Analytics jobs can fail or change reporting behavior even though the transformation code is unchanged.

**Design →** I isolated a known-good and candidate runtime using pinned Python/base images and hashed dependency locks, then ran the same SaaS models and fixtures in both through GitHub Actions.

**Validation →** I checked runtime identity, complete execution coverage, DAG and materialization contracts, compiled SQL, and actual typed data. Both environments passed 46 dbt tests; a deliberate artifact mutation proved the CI gate rejects incompatible behavior.

**Rollback →** I retained a checksummed baseline image archive and restored it on a fresh runner, rerunning the pipeline and verifying the original outputs without rebuilding dependencies.

**Business impact →** The approach reduces the risk of unexpected reporting changes and makes upgrades and recovery auditable. It demonstrates those controls in a lab; it does not claim measured production cost savings or outage prevention.
