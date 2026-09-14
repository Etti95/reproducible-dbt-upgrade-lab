"""Container-side dbt validation. Each invocation uses a fresh evidence directory."""
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import duckdb
from evidence import source_files
from export_data import export


def main():
    evidence = Path('/evidence')
    provenance = json.loads((evidence / 'source.json').read_text())
    if source_files(Path('/workspace')) != provenance['files']:
        raise SystemExit('Mounted source does not match the recorded snapshot')
    environment = os.environ['LAB_ENVIRONMENT']
    shutil.copyfile(f'environments/{environment}/requirements.txt', evidence / 'requirements.txt')
    shutil.copyfile('environments/compatibility-policy.json', evidence / 'policy.json')
    profile = Path('/tmp/lab-profile')
    profile.mkdir(exist_ok=True)
    shutil.copyfile('/workspace/profiles.yml.example', profile / 'profiles.yml')
    # These snapshots prove the runtime used in this run, not just an earlier build.
    subprocess.run([sys.executable, '/opt/lab/inventory.py', str(evidence / 'environment')], check=True)
    statuses = {}
    for command in ['deps', 'parse', 'seed', 'build', 'test']:
        output = evidence / command
        output.mkdir()
        args = ['dbt', '--no-use-colors', '--no-partial-parse',
                '--log-path', str(output / 'logs'), command,
                '--profiles-dir', str(profile), '--target', 'lab']
        if command != 'deps':
            args += ['--target-path', str(output / 'target')]
        print(f"[{os.environ['LAB_ENVIRONMENT']}] {' '.join(args)}", flush=True)
        with (output / 'console.log').open('w') as log:
            result = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT)
        print((output / 'console.log').read_text(), flush=True)
        statuses[command] = {'command': args, 'exit_code': result.returncode}
        (evidence / 'commands.json').write_text(json.dumps(statuses, indent=2) + '\n')
        if result.returncode:
            raise SystemExit(result.returncode)
    with duckdb.connect('/evidence/lab.duckdb', read_only=True) as connection:
        export(connection, evidence / 'build/target/manifest.json', evidence / 'data.json')
        cursor = connection.execute(Path('analyses/customer_health_readout.sql').read_text())
        rows = cursor.fetchall()
        with (evidence / 'customer_health.csv').open('w') as file:
            writer = csv.writer(file)
            writer.writerow([column[0] for column in cursor.description])
            writer.writerows(rows)
        summary = connection.execute('''
            select count(*) as customers, sum(mrr_usd) as mrr_usd
            from analytics.mart_customer_health
        ''').fetchone()
        print(f'Customer health: {summary[0]} customers, USD {summary[1]} MRR', flush=True)
        print(f'Readout saved to {evidence / "customer_health.csv"}', flush=True)
    if source_files(Path('/workspace')) != provenance['files']:
        raise SystemExit('Source changed during execution')


if __name__ == '__main__':
    main()
