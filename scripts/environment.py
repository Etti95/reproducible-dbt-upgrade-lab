"""Build a selected image and collect inventory using its immutable local image ID.

Usage: python3 scripts/environment.py baseline
"""
import argparse
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("environment", choices=["baseline", "candidate"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = args.output.resolve() if args.output else root / "artifacts" / args.environment / "environment"
    out.mkdir(parents=True, exist_ok=True)
    tag = f"dbt-upgrade-lab:{args.environment}"
    command = ["docker", "build", "--platform", "linux/amd64", "--progress=plain",
               "-f", f"environments/{args.environment}/Dockerfile", "-t", tag, "."]
    print(f"Building {tag}; log: {out / 'build.log'}", flush=True)
    with (out / "build.log").open("w") as log:
        subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, check=True)
    image = json.loads(subprocess.check_output(["docker", "image", "inspect", tag], text=True))[0]
    (out / "image-inspect.json").write_text(json.dumps(image, indent=2) + "\n")
    print(f"Running immutable local image {image['Id']}", flush=True)
    # Local image IDs are not registry manifest digests. Retain both when published.
    command = ["docker", "run", "--rm", "--network=none", "--platform", "linux/amd64",
               "-v", f"{out}:/evidence", image["Id"]]
    with (out / "inventory.log").open("w") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    print((out / "inventory.log").read_text())
    result.check_returncode()
    print(f"Verified {args.environment}. Evidence: {out}")


if __name__ == "__main__":
    main()
