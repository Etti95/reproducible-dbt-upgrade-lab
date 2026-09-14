"""Run both environments against one snapshot, then compare even if either fails."""
from datetime import datetime, timezone
from pathlib import Path
from evidence import snapshot
from run_project import run_environment
from compare_artifacts import compare, read


def main():
    root = Path(__file__).resolve().parents[1]
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = root / 'artifacts/comparisons' / run_id
    source = output / 'source'
    provenance = snapshot(root, source)
    for environment in ('baseline', 'candidate'):
        run_environment(environment, source, output / environment, provenance)
    report = compare(output / 'baseline', output / 'candidate', read(source / 'environments/compatibility-policy.json'))
    report.write(output / 'report')
    print(f'Compatibility exit={report.exit_code}: {output / "report/compatibility.md"}')
    raise SystemExit(report.exit_code)


if __name__ == '__main__':
    main()
