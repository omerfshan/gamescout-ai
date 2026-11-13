"""Acceptance and SOLID boundary checks for the auth -> demo import -> user games slice."""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / 'GameScout-AI-Fronted'
BACKEND = ROOT / 'GameScout-AI-Backend'
AI_SERVICE = ROOT / 'GameScout-AI-AI-Service'


class AuthImportSliceAcceptanceTests(unittest.TestCase):
    def test_renamed_root_directories_exist_and_legacy_dirs_removed(self):
        self.assertTrue(FRONTEND.is_dir(), 'GameScout-AI-Fronted missing')
        self.assertTrue(BACKEND.is_dir(), 'GameScout-AI-Backend missing')
        self.assertTrue(AI_SERVICE.is_dir(), 'GameScout-AI-AI-Service missing')
        self.assertFalse((ROOT / 'apps').exists(), 'Legacy apps/ directory should not exist')
        self.assertFalse((ROOT / 'services').exists(), 'Legacy services/ directory should not exist')

    def test_backend_domain_and_application_layers_remain_framework_free(self):
        for layer in ('Domain', 'Application'):
            folder = BACKEND / 'app' / layer
            php_files = list(folder.rglob('*.php'))
            self.assertGreaterEqual(len(php_files), 4, f'Expected PHP files in {layer}')
            for path in php_files:
                text = path.read_text(encoding='utf-8')
                self.assertIn('declare(strict_types=1);', text, f'Missing strict_types in {path}')
                self.assertNotIn('Illuminate\\', text, f'Framework leak in {layer}: {path}')
                self.assertNotIn('Laravel\\', text, f'Framework leak in {layer}: {path}')

    def test_backend_auth_and_games_ports_and_routes_wired(self):
        provider = (BACKEND / 'app/Providers/AppServiceProvider.php').read_text(encoding='utf-8')
        self.assertIn('GameCatalog::class', provider)
        self.assertIn('PgsqlGameCatalog::class', provider)
        self.assertIn('UserAuthenticator::class', provider)
        self.assertIn('SanctumUserAuthenticator::class', provider)

        routes = (BACKEND / 'routes/api.php').read_text(encoding='utf-8')
        for endpoint in ("'/auth/login'", "'/auth/me'", "'/auth/logout'", "'/imports'", "'/games'"):
            self.assertIn(endpoint, routes, f'Missing endpoint {endpoint} in routes/api.php')
        self.assertIn('auth:sanctum', routes)

        bootstrap = (BACKEND / 'bootstrap/app.php').read_text(encoding='utf-8')
        self.assertIn('InvalidCredentials', bootstrap)
        self.assertIn('invalid_credentials', bootstrap)

        migration = BACKEND / 'database/migrations/2026_11_13_000002_create_personal_access_tokens_table.php'
        self.assertTrue(migration.is_file(), 'Sanctum personal_access_tokens migration missing')
        self.assertIn('personal_access_tokens', migration.read_text(encoding='utf-8'))

        auth_tests = (BACKEND / 'tests/Feature/AuthApiTest.php').read_text(encoding='utf-8')
        self.assertIn('/api/v1/auth/login', auth_tests)
        self.assertIn('/api/v1/auth/me', auth_tests)
        self.assertIn('/api/v1/auth/logout', auth_tests)
        self.assertIn('/api/v1/imports', auth_tests)
        self.assertIn('/api/v1/games', auth_tests)

    def test_frontend_layered_auth_import_and_catalog_contract(self):
        for rel in (
            'src/domain/auth.ts',
            'src/domain/game.ts',
            'src/api/client.ts',
            'src/api/auth.ts',
            'src/api/games.ts',
            'src/features/auth/LoginForm.tsx',
            'src/features/games/GamesPage.tsx',
            'src/features/games/ImportForm.tsx',
            'src/App.tsx',
        ):
            self.assertTrue((FRONTEND / rel).is_file(), f'Missing frontend file: {rel}')

        # Domain layer must not depend on React or fetch/API client
        for domain_file in (FRONTEND / 'src/domain').glob('*.ts'):
            content = domain_file.read_text(encoding='utf-8')
            self.assertNotIn("from 'react'", content)
            self.assertNotIn('fetch(', content)

        client_ts = (FRONTEND / 'src/api/client.ts').read_text(encoding='utf-8')
        self.assertIn('Authorization', client_ts)
        self.assertIn('Bearer ', client_ts)
        self.assertIn('401', client_ts)

        auth_ts = (FRONTEND / 'src/api/auth.ts').read_text(encoding='utf-8')
        self.assertIn('/api/v1/auth/login', auth_ts)
        self.assertIn('/api/v1/auth/me', auth_ts)
        self.assertIn('/api/v1/auth/logout', auth_ts)

        games_ts = (FRONTEND / 'src/api/games.ts').read_text(encoding='utf-8')
        self.assertIn('/api/v1/games', games_ts)
        self.assertIn('/api/v1/imports', games_ts)

        # Ensure all API URLs in src/api only target same-origin /api/v1/*
        for api_file in (FRONTEND / 'src/api').glob('*.ts'):
            text = api_file.read_text(encoding='utf-8')
            urls = re.findall(r"['\"`](/api/[^'\"`$]+)", text)
            for url in urls:
                self.assertTrue(url.startswith('/api/v1/'), f'Unexpected API path {url} in {api_file.name}')
            self.assertNotIn('http://', text, f'Hardcoded external origin in {api_file.name}')
            self.assertNotIn('https://', text, f'Hardcoded external origin in {api_file.name}')

        app_tsx = (FRONTEND / 'src/App.tsx').read_text(encoding='utf-8')
        self.assertIn('LoginForm', app_tsx)
        self.assertIn('GamesPage', app_tsx)
        self.assertIn('fetchCurrentUser', app_tsx)

        games_page = (FRONTEND / 'src/features/games/GamesPage.tsx').read_text(encoding='utf-8')
        self.assertIn('OpportunityScoutPanel', games_page)
        self.assertNotIn('manual-catalog-details', games_page)
        self.assertNotIn('Sentetik demo', games_page)

    def test_autonomous_scout_slice_across_ai_backend_and_frontend(self):
        # 1. AI service CLI scout subcommand works and returns structured proposals
        import json
        import os
        import sys
        env = dict(os.environ, PYTHONPATH=str(AI_SERVICE), PYTHONDONTWRITEBYTECODE='1')
        proc = subprocess.run(
            [sys.executable, '-m', 'gamescout_ai', 'scout', '--provider', 'heuristic', '--no-network'],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertIn('scan_id', report)
        self.assertGreaterEqual(len(report['top_genre_insights']), 2)
        self.assertGreaterEqual(len(report['actionable_game_proposals']), 2)

        # 2. Backend routes and SOLID layers for Scout
        routes = (BACKEND / 'routes/api.php').read_text(encoding='utf-8')
        self.assertIn("'/scout/latest'", routes)
        self.assertIn("'/scout/runs'", routes)
        self.assertTrue((BACKEND / 'app/Domain/Scout/ScoutReportStore.php').is_file())
        self.assertTrue((BACKEND / 'app/Domain/Scout/MarketScoutRunner.php').is_file())
        self.assertTrue((BACKEND / 'app/Application/Scout/RunMarketScout.php').is_file())
        self.assertTrue((BACKEND / 'app/Infrastructure/Scout/PythonCliMarketScoutRunner.php').is_file())

        # 3. Frontend Scout domain, API, and panel
        self.assertTrue((FRONTEND / 'src/domain/scout.ts').is_file())
        self.assertTrue((FRONTEND / 'src/api/scout.ts').is_file())
        self.assertTrue((FRONTEND / 'src/features/scout/OpportunityScoutPanel.tsx').is_file())

    def test_dev_tools_bootstrap_script_and_runbook(self):
        script = ROOT / 'scripts/setup_dev_tools.sh'
        runbook = ROOT / 'docs/runbooks/local-setup.md'
        self.assertTrue(script.is_file(), 'Missing scripts/setup_dev_tools.sh')
        self.assertTrue(runbook.is_file(), 'Missing docs/runbooks/local-setup.md')

        db_config = (BACKEND / 'config/database.php').read_text(encoding='utf-8')
        self.assertIn("'pgsql'", db_config)
        self.assertIn("'sqlite'", db_config)

        phpunit_xml = (BACKEND / 'phpunit.xml').read_text(encoding='utf-8')
        self.assertIn('DB_CONNECTION', phpunit_xml)
        self.assertIn(':memory:', phpunit_xml)

        check_run = subprocess.run(
            ['bash', str(script), '--check'],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(check_run.returncode, 0, check_run.stderr)
        self.assertIn('python3', check_run.stdout)
        self.assertIn('sqlite3', check_run.stdout)


if __name__ == '__main__':
    unittest.main()
