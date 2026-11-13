"""Bounded local-model evaluation on synthetic cases; does not train weights."""
import argparse
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'GameScout-AI-AI-Service'))
from gamescout_ai.application.scout import run_market_scout
from gamescout_ai.domain.scout_models import CollectedSignalBatch, EvidenceQuote


class CaseCollector:
    def __init__(self, case):
        self.case = case

    def collect_signals(self, allow_network=True):
        case = self.case
        evidence = EvidenceQuote(source='community', source_label='Synthetic evaluation case',
            subject=case['id'], quote=case['text'], evidence_id='eval_' + case['id'],
            original_text=case['text'], signal_kind=case['signal_kind'], data_origin='synthetic_demo',
            fetched_at=datetime.now(timezone.utc).isoformat(), language='unknown')
        return CollectedSignalBatch([evidence], [], ['Synthetic evaluation, not market research.'],
                                    data_origin='synthetic_demo', source_statuses={'community': 'synthetic_demo'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Call only the configured local Ollama model; no source collection.')
    parser.add_argument('--model', default='qwen3:8b')
    parser.add_argument('--limit', type=int, choices=range(1, 11), default=3)
    args = parser.parse_args()
    cases = json.loads((ROOT / 'GameScout-AI-AI-Service/evaluation/player-needs-v1.json').read_text())['cases'][:args.limit]
    if not args.live:
        print(json.dumps({'status': 'not_run', 'training_performed': False, 'cases': cases,
                          'next': 'Use --live only when the local model is installed. Review meaning manually; reference validity is not accuracy.'}, ensure_ascii=False, indent=2))
        return 0
    os.environ['OLLAMA_MODEL'] = args.model
    results = []
    for case in cases:
        report = run_market_scout(provider='ollama', collector=CaseCollector(case), allow_network=True).to_dict()
        results.append({'case_id': case['id'], 'expectation': case['expectation'],
                        'human_review': 'pending', 'report': report})
    print(json.dumps({'training_performed': False, 'model': args.model,
                      'evaluation_origin': 'synthetic_demo', 'results': results}, ensure_ascii=False, indent=2))
    return int(any(item['report']['status'] == 'model_unavailable' for item in results))


if __name__ == '__main__':
    sys.exit(main())
