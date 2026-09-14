"""Semantic comparison with fail-closed evidence validation.

Exit 0 = compatible under this policy; 1 = failed; 2 = human review required.
Both 1 and 2 block promotion. Originals are never modified.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

from evidence import canonical, digest

COMMANDS = ('deps', 'parse', 'seed', 'build', 'test')
MANIFEST_SCHEMA = 'https://schemas.getdbt.com/dbt/manifest/v12.json'
RESULT_SCHEMA = 'https://schemas.getdbt.com/dbt/run-results/v6.json'
CONFIG_FIELDS = ('materialized', 'enabled', 'unique_key', 'incremental_strategy',
                 'on_schema_change', 'contract', 'pre-hook', 'post-hook', 'grants',
                 'column_types', 'severity', 'where', 'limit', 'fail_calc',
                 'warn_if', 'error_if', 'store_failures', 'store_failures_as')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    def reject(value):
        raise ValueError(f'Non-finite JSON number: {value}')
    return json.loads(path.read_text(), parse_constant=reject)


def sql_hash(sql):
    # Do not normalize SQL whitespace: it could be inside a string literal.
    return hashlib.sha256(sql.encode('utf-8')).hexdigest()


def metadata(artifact, schema, version):
    meta = artifact['metadata']
    require(meta['dbt_schema_version'] == schema, f'Unsupported artifact schema: {meta["dbt_schema_version"]}')
    require(meta['dbt_version'] == version, 'Artifact dbt_version differs from runtime')
    require(isinstance(meta['invocation_id'], str) and bool(meta['invocation_id']), 'Missing invocation ID')
    return meta


def normalize_manifest(manifest, compiled):
    graph, sql, documentation = {}, {}, {}
    require(isinstance(manifest['nodes'], dict) and manifest['nodes'], 'Manifest nodes missing or empty')
    # This lab has no external sources/metrics; support must be added deliberately.
    for name in ('sources', 'disabled', 'exposures', 'metrics'):
        require(manifest[name] == {}, f'Unsupported nonempty manifest section: {name}')
    for uid, node in manifest['nodes'].items():
        require(node['unique_id'] == uid, f'Node key mismatch: {uid}')
        resource = node['resource_type']
        require(resource in ('model', 'seed', 'test', 'analysis'), f'Unsupported resource: {resource}')
        config = node['config']
        require(isinstance(config['materialized'], str) and config['enabled'] is True,
                f'Missing materialization or disabled node: {uid}')
        dependencies = node['depends_on']['nodes']
        require(isinstance(dependencies, list) and all(d in manifest['nodes'] for d in dependencies),
                f'Unknown dependency in {uid}')
        relation = node['relation_name']
        if resource in ('model', 'seed'):
            require(isinstance(relation, str) and bool(relation), f'Missing relation: {uid}')
        graph[uid] = {'name': node['name'], 'resource_type': resource,
                      'dependencies': sorted(dependencies), 'relation_name': relation,
                      'config': {k: config[k] for k in CONFIG_FIELDS if k in config}}
        documentation[uid] = {'description': node['description'], 'columns': node['columns']}
        if compiled and resource in ('model', 'test'):
            require(node['compiled'] is True and isinstance(node['compiled_code'], str)
                    and node['compiled_code'].strip(), f'Missing compiled SQL: {uid}')
            sql[uid] = sql_hash(node['compiled_code'])
    return graph, sql, documentation


def execution(results, expected, graph, manifest_meta, version, command):
    meta = metadata(results, RESULT_SCHEMA, version)
    require(meta['invocation_id'] == manifest_meta['invocation_id'],
            f'{command}: manifest and run results are from different invocations')
    rows = results['results']
    ids = [r['unique_id'] for r in rows]
    require(len(ids) == len(set(ids)), f'{command}: duplicate result IDs')
    require(set(ids) == expected,
            f'{command}: missing/unexpected execution IDs: {sorted(set(ids) ^ expected)}')
    normalized, timings = {}, {}
    for row in rows:
        uid = row['unique_id']
        test = graph[uid]['resource_type'] == 'test'
        require(row['status'] == ('pass' if test else 'success'),
                f'{command}: {uid} status={row["status"]}')
        if test:
            require(type(row['failures']) is int and row['failures'] == 0,
                    f'{command}: {uid} nonzero or missing test failures')
        duration = row['execution_time']
        require(type(duration) in (int, float) and math.isfinite(duration) and duration >= 0,
                f'{command}: invalid execution time for {uid}')
        normalized[uid] = {'status': row['status'], 'failures': row['failures'],
                           'relation_name': row['relation_name']}
        timings[uid] = duration
    return normalized, timings


def load_run(path, environment, policy):
    """Validate prerequisites before admitting a run into semantic comparison."""
    require(read(path / 'completion.json')['exit_code'] == 0, 'Container validation did not finish successfully')
    require(read(path / 'policy.json') == policy, 'Recorded comparison policy differs from requested policy')
    source = read(path / 'source.json')
    require(source['schema_version'] == 1, 'Unknown source evidence schema')
    files = source['files']
    require(isinstance(files, dict) and files and source['source_sha256'] == digest(files),
            'Source manifest missing or its hash is invalid')
    for name in ('dbt_project.yml', 'profiles.yml.example', 'scripts/validate_project.py',
                 'environments/compatibility-policy.json', f'environments/{environment}/requirements.txt'):
        require(name in files, f'Source manifest missing {name}')
    require(any(name.startswith('seeds/') and name.endswith('.csv') for name in files), 'Missing seed hashes')
    runtime = read(path / 'environment/runtime.json')
    require(runtime['environment'] == environment, 'Runtime environment label mismatch')
    require(runtime['python'] == policy['python'] and runtime['machine'] == policy['machine'],
            'Unexpected Python version or platform')
    require(runtime['errors'] == [], f'Runtime errors: {runtime["errors"]}')
    require(runtime['command_exit_codes'] == {k: 0 for k in ('python-version', 'dbt-version', 'pip-freeze', 'pip-check')},
            'Missing or failing inventory command')
    for name in ('python-version', 'dbt-version', 'pip-freeze', 'pip-check'):
        require((path / f'environment/{name}.txt').read_text().strip(), f'Missing inventory output: {name}')
    lock_bytes = (path / 'requirements.txt').read_bytes()
    lock_hash = hashlib.sha256(lock_bytes).hexdigest()
    require(lock_hash == runtime['lock_sha256'] == files[f'environments/{environment}/requirements.txt'],
            'Image runtime lock does not match the source snapshot lock')
    require(hashlib.sha256((path / 'policy.json').read_bytes()).hexdigest()
            == files['environments/compatibility-policy.json'], 'Policy file hash mismatch')
    pins = dict(re.findall(r'^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?==([^\s\\]+)', lock_bytes.decode(), re.M))
    require(pins and runtime['packages'] == pins, 'Installed inventory differs from locked package versions')
    for name, version in policy['direct_dependencies'][environment].items():
        require(pins[name] == version, f'Unexpected {name} version: {pins[name]}')
    version = pins['dbt-core']
    image = read(path / 'image-inspect.json')
    require(image['Os'] == 'linux' and image['Architecture'] == 'amd64' and image['Id'].startswith('sha256:'),
            'Unexpected image platform or absent image ID')
    require(f'LAB_ENVIRONMENT={environment}' in image['Config']['Env'], 'Image environment label mismatch')
    commands = read(path / 'commands.json')
    require(set(commands) == set(COMMANDS), 'Missing required command results')
    for command in COMMANDS:
        require(commands[command]['exit_code'] == 0, f'dbt {command} failed')
        expected = ['dbt', '--no-use-colors', '--no-partial-parse', '--log-path',
                    f'/evidence/{command}/logs', command, '--profiles-dir', '/tmp/lab-profile', '--target', 'lab']
        if command != 'deps':
            expected += ['--target-path', f'/evidence/{command}/target']
        require(commands[command]['command'] == expected, f'Unexpected command/selection: {command}')
        require((path / command / 'console.log').exists(), f'Missing {command} console log')
    manifest = read(path / 'build/target/manifest.json')
    meta = metadata(manifest, MANIFEST_SCHEMA, version)
    require(meta['adapter_type'] == policy['adapter'] and meta['project_name'] == policy['project'],
            'Unexpected adapter or project metadata')
    graph, sql, documentation = normalize_manifest(manifest, compiled=True)
    counts = dict(Counter(n['resource_type'] for n in graph.values()))
    require(counts == policy['expected_counts'], f'Unexpected node counts: {counts}')
    build_ids = {k for k, n in graph.items() if n['resource_type'] in ('model', 'seed', 'test')}
    test_ids = {k for k, n in graph.items() if n['resource_type'] == 'test'}
    seed_ids = {k for k, n in graph.items() if n['resource_type'] == 'seed'}
    results, timings = {}, {}
    for command in ('parse', 'seed', 'build', 'test'):
        cm = read(path / command / 'target/manifest.json')
        cm_meta = metadata(cm, MANIFEST_SCHEMA, version)
        require(cm_meta['adapter_type'] == meta['adapter_type'] and cm_meta['project_name'] == meta['project_name'],
                f'{command}: metadata differs from build')
        require(normalize_manifest(cm, compiled=False)[0] == graph, f'{command}: graph differs within run')
        if command != 'parse':
            rr = read(path / command / 'target/run_results.json')
            expected = {'seed': seed_ids, 'build': build_ids, 'test': test_ids}[command]
            results[command], timings[command] = execution(rr, expected, graph, cm_meta, version, command)
    data = read(path / 'data.json')
    require(data['schema_version'] == 1, 'Unknown data export schema')
    relations = data['relations']
    expected = {k for k, n in graph.items() if n['resource_type'] in ('model', 'seed')}
    require(set(relations) == expected, 'Missing or extra exported relations')
    for uid, relation in relations.items():
        require(relation['relation_name'] == graph[uid]['relation_name'], f'Export relation mismatch: {uid}')
        columns = relation['columns']
        require(isinstance(columns, list) and bool(columns), f'Missing columns: {uid}')
        require(all(isinstance(c['name'], str) and c['name'] and isinstance(c['type'], str) and c['type']
                    for c in columns), f'Invalid column schema: {uid}')
        require(len({c['name'] for c in columns}) == len(columns), f'Duplicate column names: {uid}')
        rows = sorted(relation['rows'], key=canonical)
        require(all(isinstance(row, list) and len(row) == len(columns) for row in rows), f'Invalid row width: {uid}')
        require(type(relation['row_count']) is int and relation['row_count'] == len(rows), f'Row count mismatch: {uid}')
        require(relation['rows_sha256'] == digest(rows), f'Row checksum mismatch: {uid}')
        relation['rows'] = rows
    return {'source': source, 'runtime': runtime, 'image': image['Id'], 'commands': commands,
            'graph': graph, 'sql': sql, 'documentation': documentation, 'counts': counts,
            'results': results, 'timings': timings, 'relations': relations,
            'metadata': {k: meta[k] for k in ('dbt_schema_version', 'adapter_type', 'project_name', 'quoting')}}


class Report:
    def __init__(self, baseline, candidate):
        self.paths = {'baseline': str(baseline), 'candidate': str(candidate)}
        self.checks = []

    def add(self, check, baseline, candidate, result='Match', severity='High', details=None):
        self.checks.append({'check': check, 'baseline': baseline, 'candidate': candidate,
                            'result': result, 'severity': severity, 'details': details or []})

    @property
    def exit_code(self):
        if any(c['result'] == 'Fail' for c in self.checks):
            return 1
        return 2 if any(c['result'] == 'Review' for c in self.checks) else 0

    def equality(self, check, a, b, severity='High', review=False):
        if a == b:
            self.add(check, 'same', 'same', severity=severity)
            return
        details = []
        if isinstance(a, dict) and isinstance(b, dict):
            details = [{'id': k, 'baseline': a.get(k), 'candidate': b.get(k)}
                       for k in sorted(a.keys() | b.keys()) if a.get(k) != b.get(k)]
        else:
            details = [{'baseline': a, 'candidate': b}]
        self.add(check, 'differs', 'differs', 'Review' if review else 'Fail', severity, details)

    def write(self, output):
        output.mkdir(parents=True, exist_ok=True)
        status = {0: 'COMPATIBLE', 1: 'FAIL', 2: 'REVIEW REQUIRED'}[self.exit_code]
        (output / 'compatibility.json').write_text(json.dumps(
            {'schema_version': 1, 'status': status, 'exit_code': self.exit_code,
             'inputs': self.paths, 'checks': self.checks}, indent=2) + '\n')
        lines = ['# Compatibility matrix', '', f'Result: **{status}** (exit {self.exit_code}).', '',
                 'Local or CI provenance is recorded in the input runs; this report alone is not deployment approval.', '',
                 '| Check | Baseline | Candidate | Result | Severity |', '| --- | --- | --- | --- | --- |']
        def safe(value):
            return str(value).replace('|', '\\|').replace('\n', ' ')
        for c in self.checks:
            lines.append('| ' + ' | '.join(safe(c[k]) for k in ('check', 'baseline', 'candidate', 'result', 'severity')) + ' |')
        for c in self.checks:
            if c['details'] and c['result'] in ('Fail', 'Review'):
                lines += ['', f'## {c["check"]}', '', '```json', json.dumps(c['details'], indent=2), '```']
        lines += ['', 'Full per-node timing and other informational details: `compatibility.json`.', '',
                  '## Evidence', '', f'- Baseline: `{self.paths["baseline"]}`', f'- Candidate: `{self.paths["candidate"]}`', '']
        (output / 'compatibility.md').write_text('\n'.join(lines))


def compare(baseline, candidate, policy):
    report = Report(baseline, candidate)
    runs = {}
    for environment, path in [('baseline', baseline), ('candidate', candidate)]:
        try:
            require(policy['schema_version'] == 1, 'Unknown policy schema')
            runs[environment] = load_run(Path(path), environment, policy)
        except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
            report.add(f'{environment} evidence', 'required', 'invalid', 'Fail', 'Critical', [str(error)])
    if len(runs) != 2:
        return report
    a, b = runs['baseline'], runs['candidate']
    report.add('Evidence completeness and internal consistency', 'Pass', 'Pass', 'Compatible', 'Critical')
    report.equality('Source file hashes', a['source']['files'], b['source']['files'], 'Critical')
    report.equality('Source snapshot hash', a['source']['source_sha256'], b['source']['source_sha256'], 'Critical')
    report.equality('Git revision', a['source']['git_sha'], b['source']['git_sha'], 'Critical')
    for env, run in runs.items():
        if run['source']['git_dirty'] or not run['source']['git_sha']:
            report.add(f'{env} Git provenance', run['source']['git_sha'], 'uncommitted inputs',
                       'Review', 'High', ['Commit the inputs and rerun before promotion.'])
    report.add('Python', a['runtime']['python'], b['runtime']['python'], 'Match', 'Info')
    report.add('Platform', a['runtime']['machine'], b['runtime']['machine'], 'Match', 'Info')
    packages_a, packages_b = a['runtime']['packages'], b['runtime']['packages']
    changed = {k: (packages_a.get(k), packages_b.get(k)) for k in packages_a.keys() | packages_b.keys()
               if packages_a.get(k) != packages_b.get(k)}
    for package, (av, bv) in sorted(changed.items()):
        allowed = package in policy['allowed_package_changes']
        report.add(f'Package: {package}', av, bv, 'Expected' if allowed else 'Fail', 'Info' if allowed else 'Critical')
    report.add('Locked package count', len(packages_a), len(packages_b), 'Info', 'Info')
    report.add('Image ID', a['image'][:24], b['image'][:24], 'Expected', 'Info')
    for command in COMMANDS:
        report.add(f'dbt {command}', 'Pass', 'Pass', 'Compatible', 'Critical')
    for resource in ('model', 'seed', 'test', 'analysis'):
        report.add(f'{resource} node count', a['counts'][resource], b['counts'][resource], 'Match', 'High')
    report.equality('Node IDs', sorted(a['graph']), sorted(b['graph']), 'Critical')
    for field, label, severity in [('name', 'Node names', 'High'), ('resource_type', 'Resource types', 'Critical'),
                                    ('dependencies', 'DAG dependencies', 'High'), ('config', 'Materializations and selected config', 'Critical'),
                                    ('relation_name', 'Relation names', 'High')]:
        report.equality(label, {k: n[field] for k, n in a['graph'].items()},
                        {k: n[field] for k, n in b['graph'].items()}, severity)
    report.equality('Selected manifest metadata', a['metadata'], b['metadata'])
    report.equality('Compiled SQL hashes (models and tests)', a['sql'], b['sql'], review=True)
    report.equality('Model/test documentation', a['documentation'], b['documentation'], review=True)
    for command in ('seed', 'build', 'test'):
        report.equality(f'{command} node statuses and test failures', a['results'][command], b['results'][command], 'Critical')
        report.add(f'{command} node execution time sum (seconds)', round(sum(a['timings'][command].values()), 3),
                   round(sum(b['timings'][command].values()), 3), 'Info', 'Info',
                   [{'id': uid, 'baseline': seconds, 'candidate': b['timings'][command].get(uid)}
                    for uid, seconds in a['timings'][command].items()])
    report.add('Distinct tests passing', f'{a["counts"]["test"]}/{a["counts"]["test"]}',
               f'{b["counts"]["test"]}/{b["counts"]["test"]}', 'Compatible', 'Critical')
    for field, label in [('columns', 'Column names/types'), ('row_count', 'Row counts'), ('rows_sha256', 'Typed data contents')]:
        report.equality(label, {k: n[field] for k, n in a['relations'].items()},
                        {k: n[field] for k, n in b['relations'].items()})
    # Add concrete row samples without dumping entire tables into a failure report.
    for uid in a['relations'].keys() & b['relations'].keys():
        ar, br = a['relations'][uid], b['relations'][uid]
        if ar['rows_sha256'] != br['rows_sha256']:
            ac, bc = Counter(map(canonical, ar['rows'])), Counter(map(canonical, br['rows']))
            report.add(f'Changed row samples: {uid}', 'see details', 'see details', 'Fail', 'High',
                       [{'baseline_only': list((ac - bc).elements())[:5],
                         'candidate_only': list((bc - ac).elements())[:5]}])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--policy', type=Path, default=Path(__file__).resolve().parents[1] / 'environments/compatibility-policy.json')
    args = parser.parse_args()
    try:
        report = compare(args.baseline, args.candidate, read(args.policy))
    except (OSError, ValueError, KeyError, TypeError) as error:
        report = Report(args.baseline, args.candidate)
        report.add('Policy validation', 'required', 'invalid', 'Fail', 'Critical', [str(error)])
    report.write(args.output)
    print(f'Compatibility exit={report.exit_code}: {args.output / "compatibility.md"}')
    raise SystemExit(report.exit_code)


if __name__ == '__main__':
    main()
