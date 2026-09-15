# Guided implementation

## Phase 1 — Architecture and repository design

Objective: define what must remain constant and what constitutes evidence before installing tools. An environment comparison is only interpretable when its inputs are controlled.

Read the architecture and inspect the scaffold:

```bash
cd reproducible-dbt-upgrade-lab
find . -maxdepth 3 -type f | sort
cat docs/incident-context.md
```

At the end of Phase 1, the repository contained README, architecture, incident context, this guide, `.gitignore`, and `artifacts/.gitkeep`. Phase 2 adds environment definitions, locks, scripts, and measured inventory evidence.

If files are missing, check `pwd`: use the existing workspace root, not a nested `reproducible-dbt-upgrade-lab` directory. A missing `dbt` executable is expected at this stage; do not fix it with an unpinned install.

Reasoning checkpoint: if both environments build successfully and have equal row counts, but candidate MRR differs for one customer, should promotion pass? No: execution success and row counts do not establish data equivalence. The lab needs value comparisons and independently specified business invariants.

## Phase 2 — Reproducible environments

Completed: inspected Python/Docker tooling, verified published package metadata, generated hashed transitive locks in Linux/AMD64, built two images, and verified their runtime inventories. Follow [the environment exercise](environments.md) to inspect `dbt --version`, `python --version`, `pip freeze`, and Docker metadata directly. See [measured results](phase2-results.md) for exact evidence and [the real toolchain failure](toolchain-failure.md) for diagnosis and recovery.

## Phase 3 — SaaS transformations

Completed: three fixtures, explicit temporal/MRR rules, six documented models, and 46 data tests. The baseline passed deps/parse/seed/build/test. Follow [the metrics exercise](metrics.md), inspect [measured results](phase3-results.md), and rerun with `python3 scripts/run_project.py baseline`. The final customer readout is saved beside each run's command-specific artifacts.

## Phase 4 — Evidence and comparison

Completed: both environments ran the same frozen, committed source. The shared runner preserves command-specific artifacts and exports all seed/model data. The semantic comparator matched the graph, 52 SQL hashes, execution results, and nine typed relations. Follow [the comparison exercise](artifact-comparison.md), inspect [the measured matrix](compatibility_matrix.md), and run `python3 scripts/run_comparison.py`. Twenty-one comparator tests cover success, failure, and review decisions.

## Phase 5 — CI and controlled failure

Completed in hosted Actions: independent image builds from the same SHA, retained command artifacts, a passing genuine comparison, and a deliberate red comparison run. The normal run also restored the checksummed baseline image on a fresh runner and reproduced baseline outputs. See [the CI walkthrough](ci-and-rollback-drill.md) and [measured hosted results](phase5-results.md), including links to both runs. There are now 23 guardrail tests: 21 comparator checks and two drill/archive checks.

## Phase 6 — Migration and operations

Completed: the [eleven-section migration runbook](migration_runbook.md), exact recovery references, [rehearsal evidence](phase6-results.md), five-minute README, and [retrospective/interview explanation](engineering-retrospective.md). The project is public on GitHub with genuine hosted success and intentional-failure runs. Production promotion remains outside the lab scope.

## Fifteen concepts to explain after completing the lab

| Concept | Explanation grounded in this project |
| --- | --- |
| 1. Unpinned dependencies | A resolver can choose different versions or package contents at a later build; no SQL edit is needed. |
| 2. Same Git commit | Git fixes committed inputs, not future PyPI resolution or mutable base tags. |
| 3. Source vs environment reproducibility | Source hashes identify the models/fixtures; locks, platform, interpreter and image references identify runtime inputs. Both are recorded separately. |
| 4. Docker's boundary | It isolates and packages userspace. A Dockerfile with mutable inputs remains a changing build recipe. |
| 5. Mutable Python tags | A tag such as python:3.12 can refer to a new patch/base build. The lab pins a patch and an immutable platform image digest. |
| 6. Adapter/Core compatibility | The adapter implements warehouse behavior through dbt interfaces. Compatible metadata constraints do not replace import and execution tests. |
| 7. Early parse | Parse checks project structure, configuration, ref dependencies and Jinja before materializing data; it is a cheap first compatibility signal. |
| 8. Integration through build | Build executes the dependency-ordered project, including materializations and tests, exposing integration failures parse cannot. |
| 9. Manifest meaning | It describes resources, selected configuration, dependencies and compiled code for executed nodes. Presence in the manifest does not prove execution. |
| 10. Run results meaning | It records a particular command's executed node statuses, test failures and timing. A later invocation must not overwrite the evidence being compared. |
| 11. Artifact comparison | It reveals structural/compiled-contract changes despite successful SQL; typed exports additionally test data equivalence. |
| 12. Pinning vs locking | Exact direct pins constrain requested packages. A complete transitive lock with hashes fixes the approved closure and verifies allowed distribution bytes. |
| 13. Automatic failures | Missing evidence, nonzero commands, missing/skipped tests, unexpected runtime, graph/materialization/schema changes, or data mismatches fail closed. |
| 14. Human review | Compiled SQL or documentation changes and uncommitted provenance block promotion for review; timing noise alone remains informational. |
| 15. Safe rollout | Review a deliberate lock change, validate fixed inputs, retain tested images/evidence, run an isolated canary, cut over one writer, monitor, and recover by immutable reference if needed. |

Final reasoning exercise: suppose both environments produce the same USD 660 total, but one customer's MRR is overstated by 10 and another's understated by 10. The aggregate reconciles; the typed customer-level comparison must still fail. Explain which controls catch this and why an immutable image alone cannot.
