import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
from test_orchestra import load_module


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.core = load_module()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.repo = root / 'repo'
        self.repo.mkdir()
        for args in (['init'], ['config', 'user.email', 'test@example.invalid'], ['config', 'user.name', 'Test']):
            subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True)
        (self.repo / 'Project.md').write_text('Demo')
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'commit', '-m', 'base'], check=True, capture_output=True)
        self.patches = [patch.object(self.core, 'ROOT', self.repo), patch.object(self.core, 'STORE', root / 'store')]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        self.db = self.core.connect()
        self.addCleanup(self.db.close)

    def add(self, task_id, path, deps=None):
        task = {'id': task_id, 'title': task_id, 'prompt': path, 'provider': 'antigravity',
                'allowed_paths': [path], 'depends_on': deps or [],
                'checks': [['python3', '-c', f"from pathlib import Path; assert Path({path!r}).read_text() == 'ok'"]]}
        self.core.validate_task(task)
        self.db.execute('INSERT INTO tasks(id,spec,state) VALUES(?,?,?)', (task_id, json.dumps(task), 'queued'))
        self.db.commit()
        return self.db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()

    def fake(self, provider, prompt, workspace, timeout, readonly=False):
        if readonly:
            self.assertEqual(provider, 'codex')
            return '{"approved":true,"summary":"verified"}'
        self.assertEqual(provider, 'antigravity')
        path = 'a.txt' if workspace.name == 'a' else 'b.txt'
        (workspace / path).write_text('ok')
        return 'implemented'

    def test_parallel_workers_and_combined_integration(self):
        self.add('a', 'a.txt')
        self.add('b', 'b.txt')
        barrier = threading.Barrier(2)
        def ask(*args, **kwargs):
            readonly = kwargs.get('readonly', False)
            if not readonly:
                barrier.wait(timeout=10)
            return self.fake(*args, **kwargs)
        with patch.object(self.core, 'ask', side_effect=ask):
            self.assertTrue(self.core.run_queue(self.db, 2, 20, 0, 'combined'))
        combined = self.core.STORE / 'integrations/combined'
        self.assertEqual((combined / 'a.txt').read_text(), 'ok')
        self.assertEqual((combined / 'b.txt').read_text(), 'ok')
        self.assertFalse((self.repo / 'a.txt').exists())
        report = json.loads((self.core.STORE / 'reports/combined.json').read_text())
        self.assertEqual(report['state'], 'ready')

    def test_failed_check_repaired_with_history(self):
        row = self.add('a', 'a.txt')
        attempts = []
        def ask(provider, prompt, workspace, timeout, readonly=False):
            if readonly:
                return '{"approved":true,"summary":"verified"}'
            attempts.append(prompt)
            (workspace / 'a.txt').write_text('bad' if len(attempts) == 1 else 'ok')
            return 'attempt'
        with patch.object(self.core, 'ask', side_effect=ask):
            self.core.process(self.db, row, 20, max_fixes=1)
        stored = self.db.execute('SELECT * FROM tasks WHERE id="a"').fetchone()
        self.assertEqual(stored['state'], 'reviewed')
        self.assertEqual(len(json.loads(stored['attempts'])), 2)

    def test_modified_approved_workspace_cannot_integrate(self):
        row = self.add('a', 'a.txt')
        with patch.object(self.core, 'ask', side_effect=self.fake):
            self.core.process(self.db, row, 20)
            (self.core.STORE / 'workspaces/a/a.txt').write_text('tampered')
            with self.assertRaisesRegex(RuntimeError, 'changed'):
                self.core.integrate(self.db, 'bad', ['a'], 20)
        self.assertFalse((self.repo / 'a.txt').exists())

    def test_claim_serializes_overlapping_scopes(self):
        self.add('a', 'same.txt')
        self.add('b', 'same.txt')
        self.assertIsNotNone(self.core.claim(self.db))
        self.assertIsNone(self.core.claim(self.db))

    def test_parent_directory_owner_blocks_child_task(self):
        self.add('a', 'GameScout-AI-Backend')
        self.add('b', 'GameScout-AI-Backend/controller.php')
        self.assertEqual(self.core.claim(self.db)['id'], 'a')
        self.assertIsNone(self.core.claim(self.db))

    def test_rules_reach_implementer_and_reviewer(self):
        rules = self.repo / 'orchestration/RULES.md'
        rules.parent.mkdir()
        rules.write_text('RULE_MARKER: Codex owns acceptance; one writer per file.')
        row = self.add('a', 'a.txt')
        def ask(provider, prompt, workspace, timeout, readonly=False):
            self.assertIn('RULE_MARKER', prompt)
            return self.fake(provider, prompt, workspace, timeout, readonly=readonly)
        with patch.object(self.core, 'ask', side_effect=ask):
            self.core.process(self.db, row, 20)

    def test_product_implementation_cannot_use_codex(self):
        row = self.add('a', 'a.txt')
        task = json.loads(row['spec'])
        task['provider'] = 'codex'
        with self.assertRaises(ValueError):
            self.core.validate_task(task)

    def test_dependency_files_are_visible_but_protected(self):
        row = self.add('a', 'a.txt')
        with patch.object(self.core, 'ask', side_effect=self.fake):
            self.core.process(self.db, row, 20)
        child = self.add('b', 'b.txt', ['a'])
        def ask(provider, prompt, workspace, timeout, readonly=False):
            if not readonly:
                self.assertEqual((workspace / 'a.txt').read_text(), 'ok')
            return self.fake(provider, prompt, workspace, timeout, readonly=readonly)
        with patch.object(self.core, 'ask', side_effect=ask):
            self.core.process(self.db, child, 20)
            result = self.core.integrate(self.db, 'deps', ['b'], 20)
        self.assertEqual(result['state'], 'ready')


if __name__ == '__main__':
    unittest.main()
