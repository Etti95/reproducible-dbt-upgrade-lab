# Phase 6 — Runbook verification and completion

The eleven-section [migration runbook](migration_runbook.md), concise README, dependency-management tradeoffs, learning checkpoints, and [engineering retrospective/interview explanation](engineering-retrospective.md) are complete.

## Recovery rehearsal

On September 15, 2026, the documented commands were executed locally from a separate worktree at the exact hosted-tested revision:

```text
8db49b54aab14bfcc848bfa5c5c0925bcb55a851
```

Downloaded `evidence-baseline`, `evidence-candidate`, and `baseline-image` from successful hosted run `34906995612`. The recovery script verified the archive checksum and its source/Git/lock bindings, loaded the recorded image, and reran baseline validation without a build or dependency installation.

Measured outcome:

```text
simulated_rejection_exit: 1
restored_validation_exit: 0
baseline_outputs_match: true
```

All five commands passed and the restored dbt test invocation passed 46/46. Graph, compiled SQL, execution results, relation schemas and typed data matched the retained baseline. The final customer readout contains eight rows and USD 660.00 MRR.

Image ID: `sha256:99bcf404139543e153557eafa905ea1a196468814a12dce00ff5b98c52e6961b`.

Archive SHA-256: `3059005201f7310418fc7c428ebaf8f1af92abd30e845b670c281d932dc8cd29`.

Local evidence, intentionally ignored by Git:

```text
artifacts/rollback-rehearsal/
  artifacts/recovery-input/
    baseline-image/
    evidence-baseline/
    evidence-candidate/
  artifacts/recovery-drill/
    drill.json
    drill.md
    simulated-report/
    restored-baseline/
```

The worktree and downloaded archive are retained for inspection. The original main checkout was not reset. The hosted Phase 5 drill also ran on a fresh runner; this additional rehearsal validates the exact operator-facing recovery commands.

## Completion boundaries

All six lab phases are implemented and published. The genuine upgrade passed; the artifact incompatibility was explicitly simulated. No production deployment, warehouse credentials, durable image registry or branch-protection policy is configured. The runbook describes those adoption responsibilities without inventing approval or production outcomes.

The 30-day hosted artifacts remain subject to expiry. The retained local archive enables this machine's later rehearsal, but is not itself a durable production backup strategy. Source code and small measured reports remain in GitHub.
