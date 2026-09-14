# A genuine dependency failure discovered during Phase 2

This is observed tool behavior, not the planned simulated artifact mutation.

## Change and observable failure

The initial lock-generation toolchain used pip-tools 7.4.1 and pip 25.1.1. Both installed successfully inside Python 3.12.11 on Linux/AMD64. Running `pip-compile --generate-hashes` then failed:

```text
File "/usr/local/lib/python3.12/site-packages/piptools/repositories/pypi.py", line 452, in allow_all_wheels
    self.finder.find_all_candidates.cache_clear()
AttributeError: 'function' object has no attribute 'cache_clear'
```

The original logs are retained locally at `artifacts/phase2/toolchain-bootstrap.log` and `artifacts/phase2/toolchain-lock.log`. This short diagnostic excerpt is committed intentionally as portfolio evidence; complete generated logs remain ignored.

## Engineering decision and recovery

Keep pip-tools 7.4.1 and change the compiler's pip to 24.0. Hash generation then succeeded. Retain the resulting complete toolchain lock and install it in a fresh container before generating application locks. The fix is scoped to lock generation; the dbt runtime continues to use pip bundled in the digest-pinned base image.

This was recovery to a newly tested compatible pair, not rollback to an already approved production image. Later phases will exercise true rollback using a retained known-good runtime.

## Why this matters

Installation success only showed that the declared dependency constraints were satisfiable. Those constraints did not express the entire runtime API compatibility relationship. A smoke test of the tool's actual operation caught the problem before any dbt environment was approved.
