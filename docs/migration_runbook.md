# Migration runbook — dbt Core 1.10.11 to 1.10.13

Status: **lab compatibility validated; no production deployment performed or approved**.

This document records the completed lab and provides a production adoption procedure. Role names describe responsibilities, not approvals already obtained. The release owner coordinates the change, an Analytics Engineering reviewer approves metric/contracts evidence, and a platform owner approves runtime/deployment/recovery readiness. In a small team, one person may perform multiple roles with an independent reviewer.

## 1. Summary

Evaluate a deliberate Core patch upgrade while holding SQL, macros, tests, fixtures, Python, adapter, engine and platform constant. The `dbt` PyPI name-change announcement motivates the reproducibility risk; this experiment uses explicitly named `dbt-core` and `dbt-duckdb` packages and is not a Cloud CLI-to-v2 migration. See [verified facts and assumptions](incident-context.md).

Change under evaluation: Core 1.10.11 → 1.10.13. The other 53 locked application packages are unchanged. Both genuine environments passed the lab. A separate simulated materialization change was rejected by the CI gate.

The versions are a historical, bounded experiment, not a recommendation for a new production deployment today. Any later version choice requires a new reviewed lock and validation cycle.

## 2. Risk

| Failure mode | Detection/control | Engineering action |
| --- | --- | --- |
| Package name/version resolves to another CLI | Explicit package names, hashed complete locks, full pip inventory, dbt version capture | Reject unexpected package/version inventory |
| Base image tag changes | Python patch image pinned to platform-specific digest | Reuse approved digest; review updates deliberately |
| Adapter/Core/engine incompatibility | Metadata review, pip check, parse/build/test | Stop on resolver, import, parse or execution failure |
| Changed graph, materialization or contract | Selected manifest fields and relation schema comparison | Reject and investigate exact nodes |
| SQL changes that happen to fit small fixtures | Exact compiled SQL hashes | Block for human review |
| Equal row counts conceal different business data | Typed row multiset comparison and independent business tests | Reject data mismatch |
| Missing/stale artifacts appear compatible | Schema, completeness, invocation and expected-node checks | Fail closed; obtain a complete run |
| Runtime rollback leaves changed warehouse data | Independent table/input backup and restore plan | Restore/rebuild data separately; image rollback alone is insufficient |
| Retained image expires | Durable production storage before promotion | Do not approve a release without a retrievable rollback runtime |

The DuckDB lab does not test warehouse grants, real ingestion freshness, large-data performance, incremental state or external integrations. Those are additional adoption checks, not evidence this project claims to have produced.

## 3. Existing environment

| Component | Baseline |
| --- | --- |
| Python / platform | 3.12.11 / linux/amd64 |
| Base image | `python:3.12.11-slim-bookworm@sha256:c00fc7b44d844b6da22861ec24af43968a5200eac4ec607b4725d585165d6b49` |
| Core / adapter / engine | dbt-core 1.10.11 / dbt-duckdb 1.9.6 / duckdb 1.3.2 |
| Runtime pip | 25.0.1, fixed by the base image |
| Dependency lock | [baseline requirements.txt](../environments/baseline/requirements.txt), 54 application packages with hashes |
| Lock SHA-256 | `483f65e8eefc69648e47fb0799a8fce2262abae3b12b7051581c0ef38825fcc0` |
| Validated hosted image ID | `sha256:99bcf404139543e153557eafa905ea1a196468814a12dce00ff5b98c52e6961b` |
| Tested source revision | `8db49b54aab14bfcc848bfa5c5c0925bcb55a851` |

Baseline represents the lab's known-good production analogue. Its retained image is available in the successful CI run's `baseline-image` artifact; the tag `dbt-upgrade-lab:baseline` is merely a convenient local build name.

## 4. Proposed environment

| Component | Candidate |
| --- | --- |
| Python / platform / base image | Identical to baseline |
| Core / adapter / engine | dbt-core 1.10.13 / dbt-duckdb 1.9.6 / duckdb 1.3.2 |
| Dependency lock | [candidate requirements.txt](../environments/candidate/requirements.txt) |
| Lock SHA-256 | `cfde459564485c279a213dfef62088e1d40589d51fc77b767e900ff53270b0b6` |
| Validated hosted image ID | `sha256:6cdcb589ba81b54c24a545a76726f81c13bf80a69c609aca2d99513f7b40d874` |
| Tested source revision | Same as baseline |

The candidate image was built and tested in CI, but this lab archives only the baseline image for recovery. Its candidate image ID is evidence, not a promise that the runner-local image remains retrievable. Real promotion must durably retain the candidate image too; if rebuilt, validate that new image before release.

Local image IDs, base-image manifest digests and archive SHA-256 checksums identify different objects. Do not substitute one for another in a registry pull command.

## 5. Pre-upgrade checks

1. Record the baseline Git SHA, complete dependency lock, runtime inventory, source snapshot identity and image reference. Confirm the baseline is healthy before using it as a comparator.
2. Confirm package identity and exact published versions, Python requirements, adapter/Core/engine constraints, release notes and deprecations. For this lab, the selected metadata and compatibility reasoning are recorded in [environments.md](environments.md). Metadata compatibility is necessary but weaker than executing the tools.
3. Review the dependency lock diff, including transitive changes. Here only dbt-core changes. Do not regenerate locks automatically in validation CI.
4. Inspect actual runtime output and full pip inventory, rather than inferring it from Dockerfile text. The normal runners capture `dbt --version`, `python --version`, `pip freeze --all` and `pip check`.
5. Examine parse/build/test logs for deprecations or warnings. The expected `deps` warning says no packages are declared; that no-op is documented. New warnings require triage. The current comparator rejects warning test statuses but does not classify every free-text CLI warning automatically.
6. Freeze input data, dates, timezone, target/profile and source code. Confirm an environment-only change has not also changed metric definitions.
7. Before production use, confirm retained runtime availability and data recovery coverage; assign the release reviewer and the operator who can pause/revert the scheduler.

From a clean repository checkout:

```bash
python3 scripts/environment.py baseline
python3 scripts/environment.py candidate
cat artifacts/baseline/environment/dbt-version.txt
cat artifacts/candidate/environment/python-version.txt
cat artifacts/candidate/environment/pip-freeze.txt
cat artifacts/candidate/environment/pip-check.txt
```

Expected: declared versions, 54 application packages plus pip, and no broken requirements. A newly built local image may have another local ID; that build is separately validated and is not mislabeled as the retained hosted image.

## 6. Validation procedure

```bash
python3 -m unittest discover -s scripts/tests -v
python3 scripts/run_comparison.py
```

Expect 23 passing guardrail tests and a new `artifacts/comparisons/<run-id>/` directory. Both containers use the same frozen, committed source and run:

```text
dbt deps → dbt parse → dbt seed → dbt build → dbt test
```

The shared runner supplies the explicit profile/target, disables partial parsing, creates a fresh database, and routes each command's artifacts to a separate directory. `parse` catches graph/configuration/Jinja problems early; `build` exercises materializations, seeds, dependencies and tests together. The explicit seed/test invocations provide command-specific evidence, not extra distinct test coverage.

Inspect `report/compatibility.md` and `compatibility.json`, then the named nodes in `build/target/manifest.json` and `build/target/run_results.json`. Inspect the separate test results, `data.json` and `customer_health.csv`. Expected fixture outputs: six models, three seeds, 46 data tests, 52 customer-days, eight customer-health rows, and USD 660.00 end-date MRR. All nine seed/model exports must match in schema and values.

Hosted validation uses the same runners. Inspect the workflow's matrix, comparison and recovery jobs; all are required for the normal release-validation path. Do not use the intentionally red demonstration run as release evidence.

## 7. Acceptance criteria

| Requirement | Lab result / production decision |
| --- | --- |
| Same clean Git/source/seed inputs | Passed in both hosted environments |
| Declared Python/adapter/package versions; no extra packages | Passed |
| Every required command, node and test accounted for | Passed: 46/46 distinct data tests in each environment |
| Supported artifact schemas and coherent invocation IDs | Passed: manifest v12 and run-results v6 |
| Graph/config/relation contracts unchanged | Passed |
| Compiled SQL unchanged or specifically reviewed | All 52 model/test hashes matched; no waiver required |
| Exact small-fixture data equivalence | Passed across all nine relations |
| Guardrail rejection and image recovery exercised | Passed, including a fresh hosted runner |
| Production approval, durable candidate retention, operational SLOs and data rollback | Not performed; no production system is connected |

Comparator exit 0 is compatible under this policy; 1 is failure; 2 is review required. Both nonzero values block promotion. Do not change a failed test to warning or broadly ignore SQL differences to obtain approval. Document any narrowly justified change, update the intended contract through review, and rerun.

For a real deployment, promote in this order: retain the tested candidate image by durable immutable reference; obtain Analytics Engineering and platform review; run it against isolated production-like inputs; schedule one controlled canary batch with a single writer; verify output contracts and downstream consumers; then switch the scheduler to that same retained image. Keep baseline immediately available. Do not rebuild during the promotion step.

The first canary and the next two scheduled runs are a proposed observation window for this exercise, not a measured production SLO. Before adoption, set duration/cost/freshness thresholds from that warehouse's historical baseline. No numeric latency guarantee is inferred from laptop or tiny-fixture timings.

## 8. Rollback criteria

Before promotion, reject or hold a candidate for any critical failure, unresolved review item, missing evidence, or unavailable rollback runtime. Nothing needs to be deployed to discover those failures.

After promotion, pause candidate scheduling if runtime identity differs from approval, required commands/tests fail, materialization/schema/data contracts drift, downstream consumers break, or agreed freshness/cost/duration thresholds are breached. Preserve the candidate evidence and last successful batch/watermark. The operator restores the approved baseline runtime; the data owner decides whether affected relations also require restore or deterministic rebuild.

Rollback is complete only after the restored runtime and the data it serves pass validation. A successful container start alone is insufficient.

## 9. Rollback procedure

### Exact, tested lab recovery

Run from this repository's root with Docker running and GitHub CLI authenticated. These commands use a new worktree so they do not reset or overwrite your current work:

```bash
git worktree add --detach artifacts/rollback-rehearsal 8db49b54aab14bfcc848bfa5c5c0925bcb55a851
cd artifacts/rollback-rehearsal

gh run download 34906995612 --repo Etti95/reproducible-dbt-upgrade-lab \
  -n evidence-baseline -n evidence-candidate -n baseline-image \
  --dir artifacts/recovery-input

python3 scripts/failure_rollback_drill.py \
  --baseline artifacts/recovery-input/evidence-baseline/validation/result \
  --candidate artifacts/recovery-input/evidence-candidate/validation/result \
  --image-archive artifacts/recovery-input/baseline-image \
  --output artifacts/recovery-drill

cat artifacts/recovery-drill/drill.json
cat artifacts/recovery-drill/restored-baseline/customer_health.csv
```

If the named worktree/output exists from a prior rehearsal, choose new output names; the scripts intentionally refuse to overwrite evidence. The tested revision is already in repository history after a normal full clone. A shallow checkout must first fetch that exact revision.

Expected: simulated rejection exit 1, restored validation exit 0, `baseline_outputs_match: true`, and eight rows totaling USD 660.00 MRR. The script recreates the already documented hypothetical failure, then verifies, loads and executes the actual retained baseline image. It runs no pip install and no Docker build during recovery.

The retained archive must match:

```text
Image ID:
sha256:99bcf404139543e153557eafa905ea1a196468814a12dce00ff5b98c52e6961b
Archive SHA-256:
3059005201f7310418fc7c428ebaf8f1af92abd30e845b670c281d932dc8cd29
```

The script also checks the archive's source/Git/lock binding against baseline evidence. A corrupt archive, wrong source checkout or failed restored output comparison stops recovery. Preserve the error and choose another approved retained copy; do not replace it with an unpinned installation.

### Production application of the same control

Pause the candidate job and prevent concurrent writes. Point the scheduler to the retained baseline image's registry digest and recorded Git/config/input references. Restore or rebuild changed data according to the separately tested data plan, then run the same contract tests and downstream checks before resuming normal scheduling. Exact warehouse/scheduler mutation commands cannot be supplied responsibly without a real deployment target; none is configured by this lab.

Retain for every approved build: source revision, source/input snapshot identifiers, Python/platform metadata, complete locks, runtime inventories, immutable baseline and candidate images, image/archive checksums, manifests and run results by invocation, data-validation reports, CI URL/attempt, approval/exception record, scheduler/config reference, and data-restoration coordinates. Keep the prior release for at least the operational rollback window.

## 10. Post-deployment validation

In the lab, recovery validates all commands and compares original/restored graph, SQL, statuses, schemas and data. The recorded hosted recovery passed; the runbook commands are also rehearsed locally in Phase 6.

For production, confirm the scheduler actually executes the approved immutable image, inputs/watermark are complete, required tests pass without skips, key metric aggregates reconcile, grants and downstream queries still work, and freshness/duration/cost remain within the pre-agreed envelope. Check the canary and subsequent observation window; record who reviewed it before closing the migration. Keep failure/rollback artifacts even after recovery succeeds.

If only the environment is restored while the candidate's altered tables remain in service, the migration is not yet recovered. Verify the served data, not just `dbt --version`.

## 11. Evidence

- [Successful hosted CI](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34906995612), tested revision `8db49b54aab14bfcc848bfa5c5c0925bcb55a851`.
- [Compatibility matrix](ci-compatibility-matrix.md) and [hosted evidence inventory](phase5-results.md).
- [Intentional red CI run](https://github.com/Etti95/reproducible-dbt-upgrade-lab/actions/runs/34930708294) and [simulated failure report](simulated-failure-matrix.md).
- [Baseline lock](../environments/baseline/requirements.txt), [candidate lock](../environments/candidate/requirements.txt), and [comparison policy](../environments/compatibility-policy.json).
- In each downloaded `evidence-<environment>/validation/result/`: `source.json`, `commands.json`, `environment/runtime.json`, `build/target/manifest.json`, `build/target/run_results.json`, `test/target/run_results.json`, `data.json` and `customer_health.csv`.
- In `baseline-image/`: `baseline-image.tar.gz` and `image-reference.json`.
- In the hosted `failure-rollback-drill` artifact: `drill.json`, the labeled simulated report and all restored-baseline evidence.
- [Phase 6 runbook rehearsal](phase6-results.md).

The successful hosted artifacts expire October 14, 2026 UTC. A retained local/archive copy or durable production registry is required afterward; the Markdown reports alone cannot restore an image. Rebuilding from locks after expiry is a new validation event, not proof that an unavailable original image was recovered.
