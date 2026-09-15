# Phase 5 — Hosted compatibility and rollback evidence

The normal hosted workflow passed. Both environments, the semantic comparison, 23 guardrail tests, and a fresh-runner image-restoration drill succeeded.

Tested commit: `8db49b54aab14bfcc848bfa5c5c0925bcb55a851`.

Runtime-relevant source SHA-256: `9561ddec04b20e6e0171352c6644722785f2d375ea135e8e5679774db5bb8744`.

## Successful hosted run

[Run 34906995612](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34906995612) completed successfully on September 14, 2026 UTC (September 15 in Stockholm).

| Job | Result | Evidence |
| --- | --- | --- |
| Comparator tests | Pass, 23 tests | [Job log](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34906995612/job/104185882385) |
| Validate baseline | Pass, Core 1.10.11 | [Job log](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34906995612/job/104185882729) |
| Validate candidate | Pass, Core 1.10.13 | [Job log](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34906995612/job/104185882605) |
| Compatibility gate | Compatible, exit 0 | [Job log](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34906995612/job/104186459008) |
| Rejection and baseline recovery | Pass | [Job log](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34906995612/job/104186533247) |

Both real environments passed deps/parse/seed/build/test and 46 distinct dbt data tests. All 52 model/test SQL hashes and all nine typed relation exports matched. Both produced eight customer-health rows and USD 660.00 end-date MRR. See the [hosted compatibility matrix](ci-compatibility-matrix.md).

## Actual recovery evidence

The drill rejected the SIMULATED `mart_customer_health` materialization change, then loaded the retained baseline image on a fresh job runner and executed all validation commands again. Restored graph, compiled SQL, statuses, schemas and data matched the original baseline.

```text
simulated_rejection_exit: 1
restored_validation_exit: 0
baseline_outputs_match: true
```

Retained image ID:

```text
sha256:99bcf404139543e153557eafa905ea1a196468814a12dce00ff5b98c52e6961b
```

Image archive SHA-256:

```text
3059005201f7310418fc7c428ebaf8f1af92abd30e845b670c281d932dc8cd29
```

These identify the actual saved image/archive. The archive checksum is not a Docker registry manifest digest. The image was loaded, not rebuilt. Recovery used a fresh synthetic DuckDB database and did not claim to undo production data mutations.

## Downloadable evidence

The successful run retains these artifacts:

- [Baseline evidence](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34906995612/artifacts/10373256061): source/Git hashes, locks, inventories, logs, manifests, run results, data export and database.
- [Candidate evidence](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34906995612/artifacts/10372887434): corresponding independent candidate run.
- [Compatibility report](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34906995612/artifacts/10371999679): JSON and Markdown matrix.
- [Baseline image archive](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34906995612/artifacts/10373116415): roughly 107 MB, with exact image-reference metadata.
- [Failure and recovery drill](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34906995612/artifacts/10372852793): copied simulated evidence, failure report, restored baseline validation and `drill.json`.

These artifacts expire October 14, 2026 UTC under the lab's 30-day policy. The committed small reports remain available after artifact expiry; they do not replace a durable production release archive. GitHub may require sign-in to download artifacts.

Downloaded locally for verification under `artifacts/hosted/34906995612/` (excluding the large image archive). The hosted drill itself verified that archive and loaded it successfully.

## Interpretation

The Core upgrade passed the lab's genuine checks. The materialization mutation was intentionally fabricated in copied artifacts to exercise rejection. It is not a real regression in either dbt release. Image restoration and post-restore dbt execution were real.

For the full YAML explanation, local reproduction commands, and diagnostics, see [CI and rollback walkthrough](ci-and-rollback-drill.md). The completed [migration runbook](migration_runbook.md) and [engineering retrospective](engineering-retrospective.md) describe adoption and remaining production boundaries.

## Deliberately failing hosted run

[Run 34930708294](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34930708294) was manually dispatched at the same code revision with `simulate_failure=true` and finished with the expected failure.

| Job | Outcome |
| --- | --- |
| Comparator tests | Pass |
| Validate baseline | Pass |
| Validate candidate | Pass |
| Compatibility gate | **Fail**, comparator exit 1 |
| Rejection and baseline recovery drill | Skipped because its prerequisite gate failed |

The downloaded report has `simulated: true` and exactly one failing check: **Materializations and selected config**. It identifies `model.reproducible_dbt_upgrade_lab.mart_customer_health`, baseline `table` versus copied candidate `view`. All SQL/data results still match, illustrating why successful SQL alone does not establish compatibility.

See the [retained simulated failure matrix](simulated-failure-matrix.md) and [failing job log](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34930708294/job/104258357295). The workflow uploaded its failure report despite the nonzero comparison exit. Local copies are under `artifacts/hosted/34930708294/`.

This red run proves the actual CI gate rejects a hypothetical materialization change. The successful normal run above independently proves recovery from the retained baseline image. Neither run claims that Core 1.10.13 actually changed the materialization.
