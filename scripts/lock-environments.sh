#!/usr/bin/env bash
# Run from the repository root. Lock updates are a deliberate maintenance action.
set -euo pipefail
docker run --rm --platform linux/amd64 \
  -v "$PWD:/workspace" -w /workspace \
  python:3.12.11-slim-bookworm@sha256:c00fc7b44d844b6da22861ec24af43968a5200eac4ec607b4725d585165d6b49 \
  sh -ec '
    python -m pip install --require-hashes --only-binary=:all: -r environments/toolchain/requirements.txt
    pip-compile --generate-hashes --allow-unsafe --resolver=backtracking --index-url https://pypi.org/simple --output-file environments/baseline/requirements.txt environments/baseline/requirements.in
    if [ ! -f environments/candidate/requirements.txt ]; then
      cp environments/baseline/requirements.txt environments/candidate/requirements.txt
    fi
    pip-compile --generate-hashes --allow-unsafe --resolver=backtracking --index-url https://pypi.org/simple --upgrade-package dbt-core --output-file environments/candidate/requirements.txt environments/candidate/requirements.in
  '
