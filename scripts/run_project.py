"""Host entrypoint for a fresh dbt run against a frozen project snapshot."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from evidence import snapshot


def run_environment(environment, source, output, provenance, image_ref=None):
    output.mkdir(parents=True, exist_ok=False)
    (output / 'source.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(f'[{environment}] Evidence: {output}', flush=True)
    try:
        image = json.loads(subprocess.check_output(
            ['docker', 'image', 'inspect', image_ref or f'dbt-upgrade-lab:{environment}'], text=True))[0]
        (output / 'image-inspect.json').write_text(json.dumps(image, indent=2) + '\n')
        command = ['docker', 'run', '--rm', '--network=none', '--platform', 'linux/amd64',
                   '-v', f'{source}:/workspace:ro', '-v', f'{output}:/evidence',
                   image['Id'], 'python', 'scripts/validate_project.py']
        with (output / 'validation.log').open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        status = result.returncode
    except (OSError, subprocess.CalledProcessError) as error:
        (output / 'host-error.txt').write_text(str(error) + '\n')
        status = 1
    (output / 'completion.json').write_text(json.dumps({'exit_code': status}) + '\n')
    print(f'[{environment}] Exit {status}; inspect {output / "validation.log"}', flush=True)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('environment', choices=['baseline', 'candidate'])
    parser.add_argument('--output', type=Path, help='New run directory; must not already contain source/result')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    parent = args.output.resolve() if args.output else root / 'artifacts' / args.environment / 'runs' / run_id
    source = parent / 'source'
    provenance = snapshot(root, source)
    raise SystemExit(run_environment(args.environment, source, parent / 'result', provenance))


if __name__ == '__main__':
    main()
