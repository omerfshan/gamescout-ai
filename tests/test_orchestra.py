import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import json


def load_module():
    spec = importlib.util.spec_from_file_location('orchestra', Path(__file__).resolve().parents[1] / 'scripts/orchestra.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = load_module()

    def test_directory_boundary(self):
        self.assertFalse(self.core.scope_violations(['GameScout-AI-Backend/file.py'], ['GameScout-AI-Backend']))
        self.assertTrue(self.core.scope_violations(['GameScout-AI-Backend-other/file.py'], ['GameScout-AI-Backend']))

    def test_changes_include_untracked_and_committed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL, text=True).strip()
            git('init')
            git('config', 'user.email', 'test@example.invalid')
            git('config', 'user.name', 'Test')
            (root / 'base.txt').write_text('base')
            git('add', '.')
            git('commit', '-m', 'base')
            base = git('rev-parse', 'HEAD')
            (root / 'committed.txt').write_text('new')
            git('add', '.')
            git('commit', '-m', 'worker commit')
            (root / 'untracked.txt').write_text('new')
            changed = self.core.changed_paths(root, base)
            self.assertIn('committed.txt', changed)
            self.assertIn('untracked.txt', changed)

    def test_task_results_survive_new_database_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / 'repo'
            repo.mkdir()
            for args in (['init'], ['config', 'user.email', 'test@example.invalid'],
                         ['config', 'user.name', 'Test']):
                subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)
            (repo / 'Project.md').write_text('Demo project')
            subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(repo), 'commit', '-m', 'base'], check=True, capture_output=True)
            task = {'id': 'demo', 'title': 'demo', 'prompt': 'create demo',
                    'provider': 'antigravity', 'allowed_paths': ['demo.txt'],
                    'depends_on': [], 'checks': [['python3', '-c',
                    "from pathlib import Path; assert Path('demo.txt').read_text() == 'ok'"]]}
            def fake_ask(provider, prompt, workspace, timeout, readonly=False):
                if readonly:
                    return '{"approved":true,"summary":"Checked demo"}'
                (workspace / 'demo.txt').write_text('ok')
                return 'Created demo.txt'
            with patch.object(self.core, 'ROOT', repo), patch.object(self.core, 'STORE', root / 'store'), patch.object(self.core, 'ask', side_effect=fake_ask):
                db = self.core.connect()
                db.execute('INSERT INTO tasks(id,spec,state) VALUES(?,?,?)', ('demo', json.dumps(task), 'running'))
                db.commit()
                row = db.execute('SELECT * FROM tasks WHERE id="demo"').fetchone()
                self.core.process(db, row, 20)
                db.close()
                db = self.core.connect()
                restored = db.execute('SELECT * FROM tasks WHERE id="demo"').fetchone()
                self.assertEqual(restored['state'], 'reviewed')
                self.assertIn('Created demo', restored['result'])
                self.assertIn('passed', restored['checks_result'])
                self.assertIn('Checked demo', restored['review'])
                self.assertFalse((repo / 'demo.txt').exists())
                db.close()


if __name__ == '__main__':
    unittest.main()
