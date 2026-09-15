# Guided implementation

## Phase 1 — Architecture and repository design

Objective: define what must remain constant and what constitutes evidence before installing tools. An environment comparison is only interpretable when its inputs are controlled.

Read the architecture and inspect the scaffold:

```bash
cd /Users/richmore/Desktop/projects/vcontrol
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

Complete the eleven-section runbook with measured versions and real evidence paths. Practice rollback, finalize the five-minute README, then write the retrospective and interview explanation. GitHub publication and hosted CI evidence require an available GitHub repository/account; local logs will never be described as hosted CI results.
