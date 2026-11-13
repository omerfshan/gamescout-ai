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
from gamescout_ai.infrastructure.llm_providers import CompositeOpportunitySynthesizer
from gamescout_ai.infrastructure.scout_collectors import PublicMarketSignalCollector


class MarketScoutTests(unittest.TestCase):
    def test_collector_provides_multi_source_signals_offline(self) -> None:
        collector = PublicMarketSignalCollector()
        batch = collector.collect_signals(allow_network=False)
        summary = batch.sources_summary()

        self.assertGreaterEqual(summary['app_store_count'], 4)
        self.assertGreaterEqual(summary['google_play_count'], 4)
        self.assertGreaterEqual(summary['reddit_count'], 4)
        self.assertEqual(
            summary['total_signals'],
            summary['app_store_count'] + summary['google_play_count'] + summary['reddit_count'],
        )

    def test_run_market_scout_heuristic_produces_actionable_proposals(self) -> None:
        report = run_market_scout(provider='heuristic', allow_network=False)
        payload = report.to_dict()

        self.assertTrue(payload['scan_id'].startswith('scout-'))
        self.assertEqual(payload['ai_engine_used'], 'hybrid_opportunity_engine')
        self.assertEqual(len(payload['top_genre_insights']), 3)
        self.assertEqual(len(payload['actionable_game_proposals']), 3)

        first_proposal = payload['actionable_game_proposals'][0]
        self.assertIn('Şu Oyun Yapılabilir', first_proposal['concept_title'])
        self.assertTrue(first_proposal['recommended_genre'])
        self.assertTrue(first_proposal['why_people_want_this'])
        self.assertTrue(first_proposal['core_loop'])
        self.assertGreaterEqual(len(first_proposal['solved_complaints']), 2)
        self.assertGreaterEqual(len(first_proposal['evidence_quotes']), 2)

    def test_composite_synthesizer_falls_back_cleanly_when_api_key_missing(self) -> None:
        collector = PublicMarketSignalCollector()
        batch = collector.collect_signals(allow_network=False)
        synthesizer = CompositeOpportunitySynthesizer()

        with patch.dict(
            'os.environ',
            {'AI_API_KEY': '', 'GAMESCOUT_DISABLE_OLLAMA_AUTOSTART': '1'},
            clear=False,
        ):
            outcome = synthesizer.synthesize(batch, provider='openai', allow_network=True)

        self.assertEqual(outcome.ai_engine_used, 'hybrid_opportunity_engine')
        self.assertTrue(any('AI_API_KEY' in w for w in outcome.warnings))
        self.assertEqual(len(outcome.actionable_game_proposals), 3)

    def test_parse_llm_json_maps_ollama_qwen_output_and_preserves_live_quotes(self) -> None:
        collector = PublicMarketSignalCollector()
        batch = collector.collect_signals(allow_network=False)
        synthesizer = CompositeOpportunitySynthesizer()

        sample_qwen_json = {
            'top_genre_insights': [
                {
                    'genre': 'Portre Modu Taktik Roguelike',
                    'demand_badge': 'Çok Yüksek Talep',
                    'summary': 'Oyuncular kısa molalarda P2W olmayan derin taktik oyunlar istiyor.',
                    'pain_points': ['Aşırı P2W', 'Uzun oturum süresi'],
                    'requested_mechanics': ['Tek el dikey ekran', 'Anlık kayıt'],
                    'signal_count': 6,
                }
            ],
            'actionable_game_proposals': [
                {
                    'opportunity_id': 'opp-qwen-1',
                    'recommended_genre': 'Portre Modu Taktik Roguelike',
                    'concept_title': 'Zindan Sinerji Ustası',
                    'tagline': '5 dakikada derin strateji.',
                    'why_people_want_this': 'Canlı mağaza yorumlarında hızlı ve adil strateji talebi var.',
                    'core_loop': '1) Çanta diz -> 2) Savaş -> 3) Geliştir',
                    'target_audience': 'Mobil taktik severler',
                    'solved_complaints': ['P2W kaldırıldı', 'Anlık kayıt eklendi'],
                    'monetization_model': 'Tek seferlik tam sürüm paketi',
                    'risks': ['Dengeleme zorluğu'],
                    'prototype_plan': '4 haftada MVP',
                }
            ],
        }
        outcome = synthesizer._parse_llm_json(
            sample_qwen_json,
            batch=batch,
            engine_id='ollama:qwen2.5:3b',
            engine_label='Yerel Ollama LLM (qwen2.5:3b)',
        )
        self.assertEqual(outcome.ai_engine_used, 'ollama:qwen2.5:3b')
        self.assertTrue(outcome.actionable_game_proposals[0].concept_title.startswith('Şu Oyun Yapılabilir:'))
        self.assertGreaterEqual(len(outcome.actionable_game_proposals[0].evidence_quotes), 2)

    def test_invalid_provider_raises_validation_error(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            run_market_scout(provider='invalid_llm', allow_network=False)
        self.assertEqual(caught.exception.code, 'INVALID_PROVIDER')

    def test_cli_scout_subcommand_outputs_valid_json(self) -> None:
        stdout_buffer = io.StringIO()
        with patch('sys.stdout', stdout_buffer):
            exit_code = main(['scout', '--provider', 'heuristic', '--no-network'])

        self.assertEqual(exit_code, 0)
        data = json.loads(stdout_buffer.getvalue())
        self.assertIn('sources_summary', data)
        self.assertIn('top_genre_insights', data)
        self.assertIn('actionable_game_proposals', data)
        self.assertEqual(len(data['actionable_game_proposals']), 3)


if __name__ == '__main__':
    unittest.main()
