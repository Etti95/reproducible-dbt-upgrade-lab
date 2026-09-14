# Phase 2 — Measured local results

Recorded September 14, 2026. These are local Docker results, not GitHub Actions results.

Both Linux/AMD64 images built with hashed wheel-only installs. All 54 locked application packages matched their installed versions; only dbt-core differed between environments. Both images passed `pip check` and offline CLI startup. Runtime pip is 25.0.1, inherited from the base digest, in addition to the 54 locked packages.

| Check | Baseline | Candidate | Outcome |
| --- | --- | --- | --- |
| Python | 3.12.11 | 3.12.11 | Match |
| Core | 1.10.11 | 1.10.13 | Expected change |
| DuckDB adapter | 1.9.6 | 1.9.6 | Match |
| DuckDB engine | 1.3.2 | 1.3.2 | Match |
| Locked package versions verified | 54/54 | 54/54 | Pass |
| pip check | Pass | Pass | Pass |
| dbt --version exit code | 0 | 0 | Pass |
| parse/build/test/data comparison | Not run | Not run | Phase 3 onward |

## baseline

- Local image ID: `sha256:cadf12d6a947e0f880828d1bb210274a19d9579e7e05358b5edbd9ac229f6e31`
- Lock SHA-256: `483f65e8eefc69648e47fb0799a8fce2262abae3b12b7051581c0ef38825fcc0`
- Evidence directory: `artifacts/baseline/environment/`
- Inventory: `runtime.json`, `pip-freeze.txt`, `pip-check.txt`, `python-version.txt`, `dbt-version.txt`
- Build/runtime diagnostics: `build.log`, `inventory.log`, `image-inspect.json`

## candidate

- Local image ID: `sha256:fbd18254e38b562b9d4827530c3ea67fc855cfd2e05e722506c62fe86bd51b27`
- Lock SHA-256: `cfde459564485c279a213dfef62088e1d40589d51fc77b767e900ff53270b0b6`
- Evidence directory: `artifacts/candidate/environment/`
- Inventory: `runtime.json`, `pip-freeze.txt`, `pip-check.txt`, `python-version.txt`, `dbt-version.txt`
- Build/runtime diagnostics: `build.log`, `inventory.log`, `image-inspect.json`

## Interpretation

The offline version command reports that it cannot determine the latest release. This is expected because the inventory container has networking disabled; installed-version reporting succeeds. No dbt models have been executed, so this is environment smoke-test evidence, not upgrade approval.

Image IDs above identify local image configurations, not published registry manifest digests. Tags may change on rebuild. Lock checksums identify the files used in this run; image builds are not claimed to be byte-for-byte reproducible because build metadata can vary. Preserve a published image by digest for operational rollback.

The real lock-generator failure and recovery are documented in [toolchain-failure.md](toolchain-failure.md).
