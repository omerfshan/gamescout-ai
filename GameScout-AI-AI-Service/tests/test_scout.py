import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gamescout_ai.__main__ import main
from gamescout_ai.application.scout import run_market_scout
from gamescout_ai.domain.models import ValidationError
from gamescout_ai.infrastructure.scout_collectors import PublicMarketSignalCollector


class MarketScoutTests(unittest.TestCase):
    def test_offline_signals_are_explicit_synthetic(self):
        batch = PublicMarketSignalCollector().collect_signals(allow_network=False)
        self.assertEqual(batch.data_origin, 'synthetic_demo')
        self.assertTrue(batch.signals)
        self.assertTrue(all(e.data_origin == 'synthetic_demo' and e.quote == e.original_text for e in batch.signals))
        self.assertEqual(batch.live_sources_used, [])

    def test_heuristic_never_fabricates_research(self):
        report = run_market_scout(provider='heuristic', allow_network=False).to_dict()
        self.assertTrue(report['scan_id'].startswith('scout-'))
        self.assertEqual(report['status'], 'model_unavailable')
        self.assertEqual(report['data_origin'], 'synthetic_demo')
        self.assertEqual(report['actionable_game_proposals'], [])
        self.assertTrue(report['evidence_snapshot'])

    def test_invalid_provider(self):
        with self.assertRaises(ValidationError):
            run_market_scout(provider='invalid', allow_network=False)

    def test_cli_offline_reports_unavailable_honestly(self):
        stdout = io.StringIO()
        with patch('sys.stdout', stdout):
            code = main(['scout', '--provider', 'heuristic', '--no-network'])
        self.assertEqual(code, 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result['actionable_game_proposals'], [])
        self.assertEqual(result['model_metadata']['call_count'], 0)


if __name__ == '__main__':
    unittest.main()
