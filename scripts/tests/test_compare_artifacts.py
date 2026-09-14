"""Small synthetic artifacts exercise decision boundaries, not dbt's implementation."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compare_artifacts import compare, MANIFEST_SCHEMA, RESULT_SCHEMA, COMMANDS
from evidence import digest


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.policy = {
            'schema_version': 1, 'python': '3.12.11', 'machine': 'x86_64', 'adapter': 'duckdb',
            'project': 'lab', 'expected_counts': {'model': 1, 'seed': 1, 'test': 1, 'analysis': 1},
            'direct_dependencies': {'baseline': {'dbt-core': '1.10.11'}, 'candidate': {'dbt-core': '1.10.13'}},
            'allowed_package_changes': ['dbt-core']}
        files = {name: 'a' * 64 for name in ['dbt_project.yml', 'profiles.yml.example',
                 'scripts/validate_project.py', 'seeds/raw.csv']}
        self.policy_bytes = json.dumps(self.policy).encode()
        files['environments/compatibility-policy.json'] = hashlib.sha256(self.policy_bytes).hexdigest()
        for env in ('baseline', 'candidate'):
            lock = f'dbt-core=={self.policy["direct_dependencies"][env]["dbt-core"]}\n'
            files[f'environments/{env}/requirements.txt'] = hashlib.sha256(lock.encode()).hexdigest()
        for env in ('baseline', 'candidate'):
            p = self.root / env
            p.mkdir()
            version = self.policy['direct_dependencies'][env]['dbt-core']
            (p / 'requirements.txt').write_text(f'dbt-core=={version}\n')
            (p / 'policy.json').write_bytes(self.policy_bytes)
            self.put(p / 'completion.json', {'exit_code': 0})
            self.put(p / 'source.json', {'schema_version': 1, 'files': files, 'source_sha256': digest(files),
                                       'git_sha': 'b' * 40, 'git_dirty': False})
            self.put(p / 'image-inspect.json', {'Os': 'linux', 'Architecture': 'amd64', 'Id': 'sha256:' + env,
                                               'Config': {'Env': [f'LAB_ENVIRONMENT={env}']}})
            self.put(p / 'environment/runtime.json', {
                'environment': env, 'python': '3.12.11', 'machine': 'x86_64', 'errors': [],
                'command_exit_codes': {k: 0 for k in ('python-version', 'dbt-version', 'pip-freeze', 'pip-check')},
                'packages': {'dbt-core': version}, 'lock_sha256': files[f'environments/{env}/requirements.txt']})
            for name in ('python-version', 'dbt-version', 'pip-freeze', 'pip-check'):
                (p / f'environment/{name}.txt').write_text('captured\n')
            commands = {}
            for command in COMMANDS:
                target = p / command
                target.mkdir()
                (target / 'console.log').write_text('ok')
                args = ['dbt', '--no-use-colors', '--no-partial-parse', '--log-path', f'/evidence/{command}/logs',
                        command, '--profiles-dir', '/tmp/lab-profile', '--target', 'lab']
                if command != 'deps':
                    args += ['--target-path', f'/evidence/{command}/target']
                commands[command] = {'exit_code': 0, 'command': args}
                if command == 'deps':
                    continue
                nodes = {}
                for kind in ('model', 'seed', 'test', 'analysis'):
                    uid = f'{kind}.lab.example'
                    nodes[uid] = {
                        'unique_id': uid, 'resource_type': kind, 'name': 'example',
                        'config': {'materialized': {'model': 'table', 'seed': 'seed', 'test': 'test', 'analysis': 'view'}[kind],
                                   'enabled': True},
                        'depends_on': {'nodes': ['seed.lab.example'] if kind == 'model' else []},
                        'relation_name': f'"lab"."analytics"."{kind}"' if kind in ('model', 'seed') else None,
                        'description': 'description', 'columns': {}, 'compiled': True, 'compiled_code': 'select 1'}
                meta = {'dbt_schema_version': MANIFEST_SCHEMA, 'dbt_version': version,
                        'invocation_id': env + command, 'adapter_type': 'duckdb', 'project_name': 'lab', 'quoting': {}}
                self.put(target / 'target/manifest.json', {'metadata': meta, 'nodes': nodes,
                                                         'sources': {}, 'disabled': {}, 'exposures': {}, 'metrics': {}})
                if command != 'parse':
                    kinds = {'seed': ['seed'], 'build': ['model', 'seed', 'test'], 'test': ['test']}[command]
                    results = [{'unique_id': f'{kind}.lab.example', 'status': 'pass' if kind == 'test' else 'success',
                                'failures': 0 if kind == 'test' else None, 'execution_time': 0.5,
                                'relation_name': None} for kind in kinds]
                    self.put(target / 'target/run_results.json', {
                        'metadata': dict(meta, dbt_schema_version=RESULT_SCHEMA), 'results': results})
            self.put(p / 'commands.json', commands)
            rows = [[{'decimal': '10.00'}], [None]]
            relations = {f'{kind}.lab.example': {'relation_name': f'"lab"."analytics"."{kind}"',
                         'columns': [{'name': 'mrr', 'type': 'DECIMAL(18,2)'}], 'rows': rows, 'row_count': 2,
                         'rows_sha256': digest(rows)} for kind in ('model', 'seed')}
            # Sort by canonical representation, just as the exporter does.
            from evidence import canonical
            for r in relations.values():
                r['rows'] = sorted(r['rows'], key=canonical)
                r['rows_sha256'] = digest(r['rows'])
            self.put(p / 'data.json', {'schema_version': 1, 'relations': relations})

    def put(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def mutate(self, relative, fn, env='candidate'):
        p = self.root / env / relative
        value = json.loads(p.read_text())
        fn(value)
        self.put(p, value)

    def report(self):
        return compare(self.root / 'baseline', self.root / 'candidate', self.policy)

    def test_compatible(self):
        self.assertEqual(self.report().exit_code, 0)

    def test_missing_artifact_fails(self):
        (self.root / 'candidate/build/target/run_results.json').unlink()
        self.assertEqual(self.report().exit_code, 1)

    def test_unknown_schema_fails(self):
        self.mutate('build/target/manifest.json', lambda d: d['metadata'].update(dbt_schema_version='v999'))
        self.assertEqual(self.report().exit_code, 1)

    def test_missing_compiled_sql_in_both_fails(self):
        for env in ('baseline', 'candidate'):
            self.mutate('build/target/manifest.json', lambda d: d['nodes']['model.lab.example'].pop('compiled_code'), env)
        self.assertEqual(self.report().exit_code, 1)

    def test_materialization_change_fails(self):
        for command in ('parse', 'seed', 'build', 'test'):
            self.mutate(f'{command}/target/manifest.json',
                        lambda d: d['nodes']['model.lab.example']['config'].update(materialized='view'))
        report = self.report()
        self.assertEqual(report.exit_code, 1)
        self.assertTrue(any(c['check'] == 'Materializations and selected config' and c['result'] == 'Fail' for c in report.checks))

    def test_sql_change_requires_review(self):
        self.mutate('build/target/manifest.json', lambda d: d['nodes']['model.lab.example'].update(compiled_code='select 1 -- new'))
        self.assertEqual(self.report().exit_code, 2)

    def test_failed_test_fails(self):
        self.mutate('test/target/run_results.json', lambda d: d['results'][0].update(status='fail', failures=1))
        self.assertEqual(self.report().exit_code, 1)

    def test_missing_test_result_fails(self):
        self.mutate('test/target/run_results.json', lambda d: d.update(results=[]))
        self.assertEqual(self.report().exit_code, 1)

    def test_duplicate_result_fails(self):
        self.mutate('test/target/run_results.json', lambda d: d['results'].append(d['results'][0]))
        self.assertEqual(self.report().exit_code, 1)

    def test_invocation_mismatch_fails(self):
        self.mutate('build/target/run_results.json', lambda d: d['metadata'].update(invocation_id='stale-run'))
        self.assertEqual(self.report().exit_code, 1)

    def test_timing_and_generated_at_are_informational(self):
        self.mutate('test/target/run_results.json', lambda d: d['results'][0].update(execution_time=50.0))
        self.mutate('build/target/manifest.json', lambda d: d['metadata'].update(generated_at='different timestamp'))
        self.assertEqual(self.report().exit_code, 0)

    def test_row_order_ignored(self):
        self.mutate('data.json', lambda d: d['relations']['model.lab.example']['rows'].reverse())
        self.assertEqual(self.report().exit_code, 0)

    def test_equal_count_changed_money_fails(self):
        def change(d):
            r = d['relations']['model.lab.example']
            r['rows'] = [[None], [{'decimal': '11.00'}]]
            r['rows_sha256'] = digest(r['rows'])
        self.mutate('data.json', change)
        self.assertEqual(self.report().exit_code, 1)
        self.assertTrue(any(c['check'] == 'Typed data contents' and c['result'] == 'Fail' for c in self.report().checks))

    def test_missing_export_fails(self):
        self.mutate('data.json', lambda d: d['relations'].pop('model.lab.example'))
        self.assertEqual(self.report().exit_code, 1)

    def test_column_type_change_fails(self):
        self.mutate('data.json', lambda d: d['relations']['model.lab.example']['columns'][0].update(type='DOUBLE'))
        self.assertEqual(self.report().exit_code, 1)

    def test_different_source_fails(self):
        def change(d):
            d['files']['seeds/raw.csv'] = 'c' * 64
            d['source_sha256'] = digest(d['files'])
        self.mutate('source.json', change)
        self.assertEqual(self.report().exit_code, 1)

    def test_dirty_git_requires_review(self):
        self.mutate('source.json', lambda d: d.update(git_dirty=True))
        self.assertEqual(self.report().exit_code, 2)

    def test_runtime_lock_mismatch_fails(self):
        self.mutate('environment/runtime.json', lambda d: d.update(lock_sha256='bad'))
        self.assertEqual(self.report().exit_code, 1)

    def test_failing_report_is_written(self):
        (self.root / 'candidate/commands.json').unlink()
        report = self.report()
        report.write(self.root / 'report')
        self.assertEqual(json.loads((self.root / 'report/compatibility.json').read_text())['exit_code'], 1)


if __name__ == '__main__':
    unittest.main()
