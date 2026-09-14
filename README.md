# Reproducible dbt Upgrade Lab

Dependency and environment reproducibility are part of data transformation reliability.

## Current status

Phase 3 complete: two digest-pinned environments plus a working SaaS dbt project. The baseline passed all five validation commands and 46 data tests. Candidate transformation validation, artifact comparison, and CI come next. Git is initialized locally; the project has not been published to GitHub.

Start with the [environment exercise](docs/environments.md), [measured results](docs/phase2-results.md), and [a real dependency failure encountered during implementation](docs/toolchain-failure.md).

```bash
python3 scripts/environment.py baseline
python3 scripts/environment.py candidate
```

These commands build and inspect each runtime. They require a running Docker daemon and network access during image builds. Both currently verify 54 locked packages; only dbt Core differs (1.10.11 → 1.10.13).

Run the baseline transformations:

```bash
python3 scripts/run_project.py baseline
```

Expected: 6 models, 3 seeds, 46 passing data tests; eight customers and USD 660 MRR at September 7, 2026. The runner prints the new evidence directory. See [metric definitions and exercises](docs/metrics.md) and [measured baseline results](docs/phase3-results.md).

An unchanged Git commit can run differently after a rebuild if package resolution or a base image changes. This lab will hold SaaS models and seed data constant while independently building a known-good dbt Core + DuckDB environment and a candidate upgrade.

See [verified incident context](docs/incident-context.md), [architecture and decisions](docs/architecture.md), and [the phased learning guide](docs/learning-guide.md).

```mermaid
flowchart LR
    G[Same Git SHA + seeds + fixed analysis dates] --> B[Baseline image and lock]
    G --> C[Candidate image and lock]
    B --> BV[deps / parse / seed / build / test]
    C --> CV[deps / parse / seed / build / test]
    BV --> BA[Command artifacts + runtime inventory + data exports]
    CV --> CA[Command artifacts + runtime inventory + data exports]
    BA --> R[Semantic comparison + compatibility matrix]
    CA --> R
    R --> D[Reject / review / approve for promotion]
```

## Planned repository

```text
README.md
dbt_project.yml             # One shared transformation project
profiles.yml.example        # Credential-free local DuckDB profile
models/{staging,intermediate,marts}/
seeds/                     # Fixed, version-controlled source fixtures
macros/                    # Small, inspectable shared SQL logic
tests/                     # Business invariant data tests
scripts/                   # Shared runner, data export, semantic comparator
environments/{baseline,candidate}/
  Dockerfile
  requirements.in          # Exact direct dependency intent
  requirements.txt         # Generated transitive lock with hashes
artifacts/                 # Ignored generated evidence, split by environment/command
docs/                      # Architecture, guided exercises, migration and rollback
.github/workflows/dbt-compatibility.yml
```

We use this workspace as the repository root rather than adding another nested project directory. Files listed above are planned unless already present.

## Learning sequence

1. Architecture: define controlled variables and evidence.
2. Environments: verify version pairs; generate locks; build and inspect images.
3. Analytics: implement and validate subscription/customer-day metrics.
4. Evidence: run both environments and compare artifacts and data.
5. CI and failure drill: execute the same runner in Actions; prove rejection works.
6. Operations: finish migration/rollback runbooks and the engineering retrospective.

Commands and measured example results will be added as each phase is executed. No hypothetical results will be presented as successful validation.
