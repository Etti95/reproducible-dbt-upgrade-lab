# Architecture and engineering decisions

## Three different assurances

Source reproducibility means retrieving the same models, macros, configuration, and seed bytes. Environment reproducibility means retrieving the approved interpreter, CLI, adapter, engine, and dependency closure for the intended platform. Data correctness means the results satisfy the business rules. Compatibility compares behavior across environments. None alone proves the other properties.

## Controlled experiment

Both jobs use one Git SHA, the same source fixtures, fixed analysis dates, timezone, thread count, profile target name, and logical database name. Only declared environment dependencies change. Separate containers and database files prevent one run from inheriting another's state. Both database files use the same basename in separate directories so DuckDB catalog naming does not introduce avoidable relation-name differences.

Choose one canonical container platform (planned: linux/amd64) and one exact Python patch release for both environments in Phase 2. Native developer installations are convenient diagnostics, but canonical evidence comes from the specified container platform. Record the architecture rather than assuming every platform is equivalent.

## Dependencies and images

Use pip-tools to generate `requirements.txt` with the complete resolved dependency set and package hashes from exact direct requirements in `requirements.in`. Install using pip hash verification. Pin the lock-generation toolchain too. Resolve locks deliberately during upgrade work, never on each CI validation run.

An exact `dbt-core` pin alone leaves its adapter and transitive dependencies free to change. A constraints file restricts versions but does not itself request installation. Poetry and uv can manage project environments and locks; pip-tools keeps this small lab close to ordinary pip workflows. We need one implemented approach, not competing package managers.

Each Dockerfile will use a verified Python patch tag plus immutable image digest. Tags, including `python:3.12`, can move. Docker isolates and packages a runtime, but rebuilding a Dockerfile with mutable inputs can produce different bytes. Record the built image digest and preserve the image; a lockfile cannot guarantee that a package server will retain downloadable artifacts forever. Avoid unpinned operating-system installs and runtime extension downloads.

## Small, meaningful analytics DAG

Three seeds represent customers, subscriptions, and product events. Three staging models type and validate them. `int_customer_subscription_daily` evaluates active subscriptions per customer/day. `fct_customer_daily` joins usage with subscription metrics. `mart_customer_health` reports customer status as of a fixed analysis date.

Define subscription activity as `started_at <= day < ended_at`, with null end dates open-ended. Historical activity comes from dates rather than today's status. Use decimal MRR, explicit customer-day grain, and customers with no activity so tests exercise real edge cases. Document whether overlapping subscriptions are allowed and sum MRR accordingly.

Use seed `ref()` dependencies; a separate `source()` wrapper would misrepresent dbt-managed seeds as external ingestion. Include YAML documentation, generic uniqueness/not-null/relationship tests, Jinja and a small macro, plus custom tests for subscription intervals and MRR reconciliation. Start with full table builds. Add incremental materialization only with an explicit late-arrival and idempotency exercise; an untested incremental configuration would weaken the demonstration.

## Shared validation and evidence

One runner serves local Docker execution and the GitHub Actions environment matrix. Run `deps`, `parse`, `seed`, `build`, and `test`; retain exit codes and logs even on failure. With no external dbt packages, `deps` is an intentional no-op. `build` already includes seeds and tests; explicit seed/test commands are retained for learning and command-specific compatibility evidence, not counted as independent correctness coverage.

Snapshot artifacts immediately after each command: `run_results.json` is overwritten by later commands, and parse does not provide the compiled SQL needed for SQL comparison. Compare the post-build manifest and build run results, then separately compare the explicit test results. Record Python, dbt and adapter versions, pip inventory, lock hash, source/seed hashes, image digest, command arguments and exit statuses. Missing artifacts or unsupported schemas must fail closed.

Export deterministic relation schemas and sorted typed rows from this small dataset. Compare exact decimal values, nulls, dates, counts, and contents, rather than only row counts. Two equally sized tables can contain different MRR. Independently asserted expected business outcomes prevent two equally incorrect environments from appearing safe.

## Semantic comparison policy

| Signal | Policy | Reason |
| --- | --- | --- |
| Nonzero required command, failed tests, missing evidence | Automatic failure | Candidate cannot demonstrate required behavior |
| Unexpected runtime or differing source/seed inputs | Automatic failure | Experiment does not match its declared inputs |
| Missing/added node IDs, changed DAG or materialization | Automatic failure in this fixed-code lab | Structural drift requires explicit investigation |
| Changed relation names, columns, data types or data values | Automatic failure | Downstream data contracts may break |
| Unknown artifact schema version | Automatic failure until supported | Silent field omission can cause false passes |
| Compiled SQL hash difference | Review required; promotion blocked | A textual difference need not alter semantics |
| Declared dependency version change | Expected information | This is the intended experimental variable |
| Timing difference | Information initially | Tiny fixtures and shared runners are noisy |
| Invocation IDs, timestamps, absolute paths, JSON ordering | Exclude from equality, retain original evidence | These describe a run rather than transformation semantics |

Normalize arrays representing sets, select stable fields, and hash compiled SQL after only line-ending/trailing-whitespace normalization. Do not strip arbitrary SQL whitespace or literals: that can conceal meaningful changes. Compare unique IDs, names, resource types, dependencies, configuration materializations, relation names, and selected metadata explicitly. Raw JSON diff produces noise and provides no severity or missing-evidence policy.

The comparison job runs even if an environment fails and uploads its report before returning a failing status. Matrix fail-fast is disabled so both sides retain diagnostic evidence. Review-needed results block automated promotion; they are not mislabeled as proven incompatibility. Any exception must be narrow, documented, and tied to the reviewed commit and evidence.

## Failure drill and rollback

Preserve real run artifacts. Copy candidate evidence to a separate simulation directory and deliberately change one model materialization. The comparator must identify the exact node and return a failing exit code. Label the resulting report SIMULATED; it demonstrates a guardrail, not an actual dbt regression. Also test missing evidence and an ordinary compatible comparison.

Reject an unapproved candidate and rerun the retained baseline image by digest against an isolated database. Production retention must bind Git SHA/tag, image digest, dependency locks, seed/input snapshot identifiers, runtime inventory, artifacts and approval evidence. Tags are convenient names; digests identify image content. Environment rollback does not undo changed warehouse data: migrations that alter persistent tables also need a data restore or rebuild plan.

## Repository design

Keep one dbt project at the root and environment definitions in two folders. Duplicating models would introduce a second changing variable. Keep generated artifacts out of Git; CI retains complete evidence and the repository may later retain a clearly labeled small report example. Scripts remain separate from dbt custom SQL tests. Documentation explains decisions and operational steps rather than hiding them inside shell wrappers.
