"""Shared evidence format; no dbt or third-party imports on the host."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

SOURCE_DIRECTORIES = ('models', 'seeds', 'macros', 'tests', 'analyses', 'scripts', 'environments', '.github')
SOURCE_FILES = ('dbt_project.yml', 'profiles.yml.example', '.python-version', '.dockerignore')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def source_files(root):
    root = Path(root)
    files = [root / name for name in SOURCE_FILES]
    for directory in SOURCE_DIRECTORIES:
        files.extend(p for p in (root / directory).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)}


def snapshot(root, destination):
    """Freeze runtime-relevant files once. Reject a source edit during copying."""
    before = source_files(root)
    destination.mkdir(parents=True, exist_ok=False)
    for name in before:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
    if before != source_files(root) or before != source_files(destination):
        raise RuntimeError('Source changed while making the snapshot; rerun')
    sha = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, text=True, capture_output=True)
    status = subprocess.run(['git', 'status', '--porcelain'], cwd=root, text=True, capture_output=True)
    ci = None
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        ci = {'run_url': f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
              'run_attempt': os.environ['GITHUB_RUN_ATTEMPT'], 'event': os.environ['GITHUB_EVENT_NAME']}
    return {'schema_version': 1, 'files': before, 'source_sha256': digest(before), 'ci': ci,
            'git_sha': sha.stdout.strip() if sha.returncode == 0 else None,
            'git_dirty': bool(status.stdout) or status.returncode != 0}
