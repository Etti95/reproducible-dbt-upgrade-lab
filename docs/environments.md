# Phase 2 — Build the runtime before building the models

## Objective

An approved environment is more than three direct version pins. We need an exact interpreter, operating-system image, platform, dependency closure, and evidence of what actually executes.

| Component | Baseline | Candidate |
| --- | --- | --- |
| Platform | linux/amd64 | linux/amd64 |
| Python | 3.12.11 | 3.12.11 |
| dbt-core | 1.10.11 | 1.10.13 |
| dbt-duckdb | 1.9.6 | 1.9.6 |
| DuckDB engine | 1.3.2 | 1.3.2 |

These historical versions create a bounded patch-upgrade experiment. They are not a claim that this is today's recommended production stack. Both Core versions are published for Python >=3.9. Adapter 1.9.6 declares Core >=1.8.0 and DuckDB >=1.0.0; those constraints admit our choices, but installation and behavioral validation remain necessary.

Sources: [baseline Core metadata](https://pypi.org/pypi/dbt-core/1.10.11/json), [candidate Core metadata](https://pypi.org/pypi/dbt-core/1.10.13/json), [adapter metadata](https://pypi.org/pypi/dbt-duckdb/1.9.6/json), [engine metadata](https://pypi.org/pypi/duckdb/1.3.2/json).

## What is pinned

Both Dockerfiles use this platform-specific Python image:

```text
python:3.12.11-slim-bookworm@sha256:c00fc7b44d844b6da22861ec24af43968a5200eac4ec607b4725d585165d6b49
```

The digest was resolved with `docker buildx imagetools inspect python:3.12.11-slim-bookworm`. It identifies the linux/amd64 manifest, rather than the multi-platform index. We explicitly pass `--platform linux/amd64`; Apple Silicon runs it through Docker's emulation. Performance measurements here must not be compared to native Linux timings.

The base digest also fixes its bundled pip (25.0.1). Runtime installs use `--require-hashes --only-binary=:all:`. Exact versions prevent resolution drift; hashes verify allowed distribution bytes; wheels avoid an extra unpinned source-build toolchain. If no compatible wheel exists, the build fails rather than silently compiling one.

The lock compiler runs separately: pip-tools 7.4.1 with pip 24.0 and a hashed toolchain lock. It is not part of the dbt runtime. Generating a lock is intentionally a dependency-resolution event; consuming an existing lock is not. The first toolchain lock was bootstrapped from direct pins, then consumed in a fresh container before generating dbt locks. The retained toolchain lock fixes that bootstrap's selected transitive dependencies for subsequent use.

## Build and inspect

Start Docker Desktop, then from the repository root:

```bash
python3 scripts/environment.py baseline
python3 scripts/environment.py candidate
```

The host Python only orchestrates Docker using its standard library. Its version is not the dbt runtime version. Each command builds the selected Dockerfile, records image metadata, then runs the resulting immutable local image ID with networking disabled to capture its inventory.

Inspect the actual evidence:

```bash
cat artifacts/baseline/environment/dbt-version.txt
cat artifacts/candidate/environment/dbt-version.txt
cat artifacts/baseline/environment/python-version.txt
cat artifacts/baseline/environment/pip-freeze.txt
cat artifacts/baseline/environment/pip-check.txt
cat artifacts/baseline/environment/runtime.json
docker image inspect dbt-upgrade-lab:baseline
```

Expected: Python 3.12.11, Core 1.10.11 versus 1.10.13, adapter 1.9.6, no broken requirements, and an empty `errors` array in each runtime report. The exact measured outcome is recorded separately in `phase2-results.md` once validation completes. A version banner may recommend newer packages; that is not permission to change the lock.

Inspect the direct intent and the complete lock:

```bash
cat environments/baseline/requirements.in
diff -u environments/baseline/requirements.txt environments/candidate/requirements.txt
```

Unlike dbt JSON artifacts, dependency lock text is suitable for a review diff. Header and hash changes need context; verify which package versions actually changed. The candidate is initially seeded from the baseline lock before recompilation so the resolver preserves existing pins when compatible. Future upstream changes do not silently refresh existing pins. Updating transitive dependencies requires an intentional lock change and the same validation process.

## Deliberately regenerate locks

Routine builds use committed locks. Only run the following when evaluating dependency changes:

```bash
bash scripts/lock-environments.sh
```

This installs the hashed compiler toolchain in the pinned container, resolves baseline intent, and upgrades the candidate's selected Core requirement. Review the resulting lock diff before treating it as approved. Do not run this command automatically as part of a validation CI build.

## Diagnose failures

- Docker socket unavailable: start Docker Desktop and inspect `docker version`.
- Build failure: inspect `artifacts/<environment>/environment/build.log`. A resolver conflict, missing wheel, or hash mismatch is evidence to investigate; do not remove the pins or hash checks to make it pass.
- CLI starts but `pip check` fails: declared package requirements conflict. Capture both outputs; installed does not mean compatible.
- Runtime version mismatch: inspect the lock, image ID, and `pip-freeze.txt`; the wrong image or an altered runtime may have been used.
- `exec format error` or unexpectedly slow startup: check Docker's Linux/AMD64 emulation. The canonical platform is explicit even on an ARM host.

## Rollback references at this stage

The scripts retain the built image ID in `image-inspect.json`. A local image ID is not a registry manifest digest, and `RepoDigests` can be empty until an image is pulled/published. Do not invent a registry digest or present a mutable tag as immutable. Later CI/promotion work will bind the published digest to the Git commit and approval evidence.

At this phase, rebuilding baseline uses its retained Dockerfile, base digest, and hashed lock. Reusing the retained baseline image ID avoids rebuilding at all. Neither approach restores warehouse data altered by an upgrade.

## Reasoning checkpoint

If the candidate changes only `dbt-core` in `requirements.in`, but ten transitive packages change in its lock, what are you testing? The whole changed environment. Investigate those extra changes, preserve compatible baseline pins where possible, and describe the true scope in the upgrade report.

## Why this package-management approach

A filename does not determine reproducibility: `requirements.txt` can contain unbounded ranges or a complete hash-locked dependency set. Inspect its contents and the installation command.

| Option | What it provides | Limit / reason for this lab's choice |
| --- | --- | --- |
| Handwritten requirements | Simple package names and exact direct pins | Direct pins alone leave transitive resolution open |
| [Constraints file](https://pip.pypa.io/en/stable/user_guide/#constraints-files) | Bounds versions for packages requested elsewhere | Does not request installation or inherently lock every transitive dependency |
| [pip-tools](https://pip-tools.readthedocs.io/en/stable/) | Compiles readable direct intent into resolved pip-compatible requirements with hashes | Lock generation must use the intended interpreter/platform and a tested compiler toolchain; chosen here for transparency |
| [Poetry](https://python-poetry.org/docs/basic-usage/) | Project/dependency management with a resolver and lock | Useful for a broader Python application; adds a workflow this small dbt lab does not need |
| [uv](https://docs.astral.sh/uv/concepts/projects/sync/) | Environment/dependency management and lock/compile workflows | Also a valid choice; introducing a second resolver would add another variable here |
| Lockfile | Records an approved resolved dependency set; format may also capture hashes/platform rules | Must actually be consumed in a locked install; it cannot ensure artifacts remain hosted forever |
| Docker image digest | Identifies an immutable registry image manifest for retrieval | Requires image availability; does not establish SQL correctness or restore changed data |

The risky recipe is:

```dockerfile
RUN pip install dbt
```

Explicit direct pins improve package identity and scope, but still leave transitives unresolved:

```dockerfile
RUN pip install dbt-core==1.10.11 dbt-duckdb==1.9.6 duckdb==1.3.2
```

The actual lab consumes the complete reviewed lock:

```dockerfile
RUN python -m pip install --no-cache-dir --require-hashes --only-binary=:all: -r /opt/lab/requirements.txt
```

Combined with the digest-pinned base image and explicit platform, this controls the installation inputs. Keeping the built image provides the recovery path when dependency servers are unavailable. See the [migration runbook](migration_runbook.md) for the exact retained image and archive references.
