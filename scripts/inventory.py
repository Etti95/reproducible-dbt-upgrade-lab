"""Capture and verify the runtime before any transformation is allowed to run."""
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys


def main():
    environment = os.environ["LAB_ENVIRONMENT"]
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "/evidence")
    out.mkdir(parents=True, exist_ok=True)
    lock = Path("/opt/lab/requirements.txt")
    expected = dict(re.findall(r"^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?==([^\s\\]+)", lock.read_text(), re.M))
    if not {"dbt-core", "dbt-duckdb", "duckdb"}.issubset(expected):
        raise SystemExit("Runtime lock is missing required direct dependencies")
    installed = {name: metadata.version(name) for name in expected}
    errors = [f"{name}: expected {version}, found {installed[name]}"
              for name, version in expected.items() if installed[name] != version]
    if platform.python_version() != "3.12.11":
        errors.append("Python differs from 3.12.11")
    if metadata.version("pip") != "25.0.1":
        errors.append("pip differs from the digest-pinned base image's 25.0.1")
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        errors.append("Canonical platform must be Linux/x86_64")
    commands = {
        "python-version": [sys.executable, "--version"],
        "dbt-version": ["dbt", "--version"],
        "pip-freeze": [sys.executable, "-m", "pip", "freeze", "--all"],
        "pip-check": [sys.executable, "-m", "pip", "check"],
    }
    statuses = {}
    for label, command in commands.items():
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out / f"{label}.txt").write_text(result.stdout)
        statuses[label] = result.returncode
        print(f"[{environment}] {label}: exit={result.returncode}\n{result.stdout}", flush=True)
        if result.returncode:
            errors.append(f"{label} failed")
    report = {
        "environment": environment,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
        "packages": installed,
        "command_exit_codes": statuses,
        "errors": errors,
    }
    (out / "runtime.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if errors:
        raise SystemExit("Runtime verification failed: " + "; ".join(errors))


if __name__ == "__main__":
    main()
