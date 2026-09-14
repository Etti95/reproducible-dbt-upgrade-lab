"""Verify that a simulation preserves original evidence and corrupt archives fail early."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from image_archive import restore
from simulate_candidate import simulate, NODE


class FailureDrillTests(unittest.TestCase):
    def test_simulation_preserves_originals_and_marks_every_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / 'original', root / 'simulated'
            originals = {}
            for command in ('parse', 'seed', 'build', 'test'):
                path = source / command / 'target/manifest.json'
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps({'nodes': {NODE: {'config': {'materialized': 'table'}}}}))
                originals[path] = path.read_bytes()
            simulate(source, output)
            for path, original in originals.items():
                self.assertEqual(path.read_bytes(), original)
                changed = json.loads((output / path.relative_to(source)).read_text())
                self.assertEqual(changed['nodes'][NODE]['config']['materialized'], 'view')
            self.assertTrue(json.loads((output / 'SIMULATED.json').read_text())['simulated'])
            with self.assertRaises(FileExistsError):
                simulate(source, output)

    def test_corrupt_archive_is_not_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'baseline-image.tar.gz').write_bytes(b'corrupt archive')
            (root / 'image-reference.json').write_text(json.dumps({'schema_version': 1, 'archive_sha256': 'wrong'}))
            with patch('image_archive.subprocess.run') as docker:
                with self.assertRaisesRegex(ValueError, 'checksum'):
                    restore(root)
                docker.assert_not_called()


if __name__ == '__main__':
    unittest.main()
