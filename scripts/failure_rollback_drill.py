"""Assert simulated rejection, restore the retained baseline image, and revalidate."""
import argparse
import json
from pathlib import Path

from compare_artifacts import compare, load_run, read
from evidence import snapshot
from image_archive import restore
from run_project import run_environment
from simulate_candidate import simulate, NODE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--image-archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    policy = read(root / 'environments/compatibility-policy.json')
    # A drill must start from real, passing evidence; otherwise rejection proves little.
    genuine = compare(args.baseline, args.candidate, policy)
    if genuine.exit_code != 0:
        raise SystemExit('Original environment comparison must pass before the drill')
    simulate(args.candidate, output / 'candidate-simulated')
    rejected = compare(args.baseline, output / 'candidate-simulated', policy)
    rejected.write(output / 'simulated-report')
    detected = any(c['check'] == 'Materializations and selected config' and c['result'] == 'Fail'
                   and any(d.get('id') == NODE for d in c['details']) for c in rejected.checks)
    if rejected.exit_code != 1 or not detected:
        raise SystemExit('Guardrail did not reject the intended simulated materialization change')
    baseline = load_run(args.baseline, 'baseline', policy)
    image = restore(args.image_archive)
    for field, expected in [('image_id', baseline['image']), ('git_sha', baseline['source']['git_sha']),
                            ('source_sha256', baseline['source']['source_sha256']),
                            ('lock_sha256', baseline['runtime']['lock_sha256'])]:
        if image[field] != expected:
            raise ValueError(f'Archive does not belong to validated baseline: {field}')
    provenance = snapshot(root, output / 'source')
    if provenance['source_sha256'] != image['source_sha256'] or provenance['git_sha'] != image['git_sha'] or provenance['git_dirty']:
        raise ValueError('Rollback must use the same clean source revision as the validated baseline')
    result = run_environment('baseline', output / 'source', output / 'restored-baseline', provenance,
                             image_ref=image['image_id'])
    if result:
        raise SystemExit('Restored baseline validation failed')
    restored = load_run(output / 'restored-baseline', 'baseline', policy)
    for field in ('graph', 'sql', 'results', 'relations', 'metadata', 'documentation'):
        if restored[field] != baseline[field]:
            raise ValueError(f'Restored baseline differs: {field}')
    evidence = {'simulated_rejection_exit': rejected.exit_code, 'detected_node': NODE,
                'decision': 'Reject simulated candidate; reuse retained baseline image',
                'rollback_image_id': image['image_id'], 'archive_sha256': image['archive_sha256'],
                'git_sha': image['git_sha'], 'source_sha256': image['source_sha256'],
                'restored_validation_exit': result, 'baseline_outputs_match': True}
    (output / 'drill.json').write_text(json.dumps(evidence, indent=2) + '\n')
    (output / 'drill.md').write_text(
        '# Failure and rollback drill — PASS\n\n'
        'The materialization change is SIMULATED; the baseline image restoration and dbt rerun are real.\n\n'
        f'- Change: `{NODE}` from table to view in a copied artifact bundle.\n'
        '- Observable failure: comparator exit 1, identifying the exact changed node.\n'
        '- Decision: reject that hypothetical candidate.\n'
        f'- Rollback: verify archive checksum, load `{image["image_id"]}`, and run it without rebuilding.\n'
        '- Validation: deps/parse/seed/build/test passed; all restored baseline outputs matched.\n\n'
        'This exercises environment recovery into a fresh DuckDB database. It does not undo production data writes.\n')
    print((output / 'drill.md').read_text())


if __name__ == '__main__':
    main()
