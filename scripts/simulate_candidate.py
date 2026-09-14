"""Copy candidate evidence and inject a labeled hypothetical materialization change."""
import argparse
import json
from pathlib import Path
import shutil

NODE = 'model.reproducible_dbt_upgrade_lab.mart_customer_health'


def simulate(candidate, output):
    shutil.copytree(candidate, output)  # Refuse to overwrite an existing drill.
    mutation = {'simulated': True, 'node': NODE, 'field': 'config.materialized',
                'before': 'table', 'after': 'view',
                'explanation': 'Hypothetical artifact change only; dbt did not generate this change.'}
    for command in ('parse', 'seed', 'build', 'test'):
        path = output / command / 'target/manifest.json'
        manifest = json.loads(path.read_text())
        if manifest['nodes'][NODE]['config']['materialized'] != 'table':
            raise ValueError('Drill requires the original table materialization')
        manifest['nodes'][NODE]['config']['materialized'] = 'view'
        path.write_text(json.dumps(manifest) + '\n')
    (output / 'SIMULATED.json').write_text(json.dumps(mutation, indent=2) + '\n')
    print(f'SIMULATED: {NODE} table -> view in copied evidence: {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    simulate(args.candidate, args.output)


if __name__ == '__main__':
    main()
