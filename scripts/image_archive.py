"""Save/load a validated Docker image with an archive checksum and exact image ID."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(evidence, output):
    from compare_artifacts import load_run, read
    run = load_run(evidence, 'baseline', read(evidence / 'policy.json'))
    output.mkdir(parents=True, exist_ok=False)
    archive = output / 'baseline-image.tar.gz'
    with tempfile.TemporaryDirectory() as directory:
        tar = Path(directory) / 'image.tar'
        subprocess.run(['docker', 'save', '--output', str(tar), run['image']], check=True)
        with tar.open('rb') as src, gzip.open(archive, 'wb', compresslevel=1) as dst:
            shutil.copyfileobj(src, dst)
    record = {'schema_version': 1, 'image_id': run['image'], 'archive_sha256': file_sha(archive),
              'source_sha256': run['source']['source_sha256'], 'git_sha': run['source']['git_sha'],
              'lock_sha256': run['runtime']['lock_sha256']}
    (output / 'image-reference.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


def restore(directory):
    record = json.loads((directory / 'image-reference.json').read_text())
    archive = directory / 'baseline-image.tar.gz'
    if record['schema_version'] != 1 or file_sha(archive) != record['archive_sha256']:
        raise ValueError('Image archive checksum/schema mismatch')
    subprocess.run(['docker', 'load', '--input', str(archive)], check=True)
    image = json.loads(subprocess.check_output(['docker', 'image', 'inspect', record['image_id']], text=True))[0]
    if image['Id'] != record['image_id'] or image['Architecture'] != 'amd64' or image['Os'] != 'linux':
        raise ValueError('Restored image identity/platform mismatch')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['save', 'restore'])
    parser.add_argument('directory', type=Path)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    if args.operation == 'save':
        if args.evidence is None:
            parser.error('--evidence is required for save')
        save(args.evidence, args.directory)
    else:
        print(json.dumps(restore(args.directory), indent=2))


if __name__ == '__main__':
    main()
