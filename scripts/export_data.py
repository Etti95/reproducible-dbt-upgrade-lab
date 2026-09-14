"""Export small lab relations as typed, sorted row multisets (duplicates retained)."""
from datetime import date, datetime
from decimal import Decimal
import json
from pathlib import Path
from evidence import canonical, digest


def cell(value):
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, Decimal):
        return {'decimal': str(value)}
    if isinstance(value, datetime):
        return {'timestamp': value.isoformat()}
    if isinstance(value, date):
        return {'date': value.isoformat()}
    raise TypeError(f'Unsupported export type: {type(value).__name__}')


def quoted(name):
    return '"' + name.replace('"', '""') + '"'


def export(connection, manifest_path, output):
    manifest = json.loads(Path(manifest_path).read_text())
    relations = {}
    for uid, node in sorted(manifest['nodes'].items()):
        if node['resource_type'] not in ('model', 'seed'):
            continue
        name = '.'.join(quoted(node[key]) for key in ('database', 'schema', 'alias'))
        columns = [{'name': c[0], 'type': c[1]}
                   for c in connection.execute(f'DESCRIBE SELECT * FROM {name}').fetchall()]
        cursor = connection.execute(f'SELECT * FROM {name}')
        rows = sorted(([cell(v) for v in row] for row in cursor.fetchall()), key=canonical)
        relations[uid] = {'relation_name': node['relation_name'], 'columns': columns,
                          'row_count': len(rows), 'rows': rows, 'rows_sha256': digest(rows)}
    Path(output).write_text(json.dumps({'schema_version': 1, 'relations': relations},
                                      indent=2, ensure_ascii=False) + '\n')
