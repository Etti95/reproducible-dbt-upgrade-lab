# Incident context

Checked September 14, 2026.

## Verified source statements

The [dbt package page on PyPI](https://pypi.org/project/dbt/) announces that from September 14, 2026, the package name installs dbt v2 instead of the Cloud CLI. The retrieved listing still identifies 1.0.0.40.21 as stable and lists v2 prereleases. This verifies the published migration warning, not the actual resolver outcome on a particular machine at a particular time.

The [2.0.0rc218 package page](https://pypi.org/project/dbt/2.0.0rc218/) describes a Fusion engine CLI implemented in Rust. These package descriptions establish that the shared package name spans different CLI products.

The [DuckDB adapter documentation on PyPI](https://pypi.org/project/dbt-duckdb/) describes its dbt Core integration. Exact dependency compatibility must be checked against metadata for the versions selected in Phase 2; a broad support statement is not proof that a particular pair works.

The migration documentation linked by PyPI could not be retrieved during this check. No conclusions here depend on its contents.

## Lab assumptions and boundaries

- Baseline represents an approved production environment, not a claim about the user's real production stack.
- Baseline and candidate will both use explicitly pinned `dbt-core`, `dbt-duckdb`, and `duckdb`. Exact versions are deliberately pending metadata inspection and installation tests.
- We will not describe a Core-to-Core upgrade as a reproduction of the Cloud CLI-to-v2 transition.
- A separately labeled controlled artifact mutation will demonstrate detection if both genuine environments pass.
- A clean installation or upgrade can resolve differently when its allowed dependency set changes. A plain install into an already satisfied environment does not necessarily upgrade it.
- Runtime drift is possible without SQL or Git changes. The incident illustrates this mechanism; compatibility must still be measured.
