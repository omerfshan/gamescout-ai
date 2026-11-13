"""Codex acceptance checks for the Antigravity Discovery implementation."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DiscoveryAcceptance(unittest.TestCase):
    def game(self, app='demo.app', platform='android', title='DEMO game'):
        return dict(game_id='game-1', platform=platform, external_app_id=app,
                    title=title, developer_profile='unknown', source_record_id='demo-source',
                    normalized_genres=['puzzle'])

    def invoke(self, games, *args, origin='synthetic_demo'):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_text(json.dumps(dict(schema_version='1.0.0', data_origin=origin, games=games)))
            env = dict(os.environ, PYTHONPATH=str(ROOT / 'GameScout-AI-AI-Service'), PYTHONDONTWRITEBYTECODE='1')
            return subprocess.run([sys.executable, '-m', 'gamescout_ai', 'discover', str(path),
                                   '--platform', 'android', *args], cwd=ROOT, env=env,
                                  capture_output=True, text=True, timeout=10)

    def test_duplicate_collapse_keeps_platform_boundary(self):
        result = self.invoke([self.game(), self.game(), self.game(platform='ios')])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['input_count'], 3)
        self.assertEqual(data['deduplicated_count'], 2)
        self.assertEqual(data['returned_count'], 1)
        self.assertEqual(data['data_origin'], 'synthetic_demo')
        self.assertTrue(data.get('demo_label'))

    def test_conflicting_duplicate_rejected(self):
        result = self.invoke([self.game(), self.game(title='Different game')])
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)
        self.assertIsInstance(json.loads(result.stderr), dict)

    def test_real_data_not_silently_treated_as_demo(self):
        result = self.invoke([self.game()], origin='licensed_import')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')

    def test_no_match_is_insufficient_data(self):
        result = self.invoke([self.game()], '--genre', 'racing')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['status'], 'insufficient_data')
        self.assertEqual(data['games'], [])

    def test_invalid_numeric_identifier_rejected(self):
        game = self.game()
        game['external_app_id'] = 123
        self.assertEqual(self.invoke([game]).returncode, 2)


if __name__ == '__main__':
    unittest.main()
