"""Application use case for the AI Game Opportunity Researcher (Scout)."""
from datetime import datetime, timezone
import uuid

from gamescout_ai.domain.models import ValidationError
from gamescout_ai.domain.scout_models import (
    MarketScoutReport,
    OpportunitySynthesizerPort,
    SignalCollectorPort,
)
from gamescout_ai.infrastructure.llm_providers import CompositeOpportunitySynthesizer
from gamescout_ai.infrastructure.scout_collectors import PublicMarketSignalCollector

VALID_PROVIDERS = ('auto', 'ollama', 'openai', 'gemini', 'heuristic')


def run_market_scout(
    provider: str = 'auto',
    allow_network: bool = True,
    collector: SignalCollectorPort | None = None,
    synthesizer: OpportunitySynthesizerPort | None = None,
) -> MarketScoutReport:
    normalized_provider = (provider or 'auto').strip().lower()
    if normalized_provider not in VALID_PROVIDERS:
        raise ValidationError(
            'INVALID_PROVIDER',
            f'Geçersiz AI sağlayıcısı: {provider}. Geçerli değerler: {", ".join(VALID_PROVIDERS)}',
        )

    signal_collector = collector or PublicMarketSignalCollector()
    opportunity_synthesizer = synthesizer or CompositeOpportunitySynthesizer()

    batch = signal_collector.collect_signals(allow_network=allow_network)
    outcome = opportunity_synthesizer.synthesize(
        batch=batch,
        provider=normalized_provider,
        allow_network=allow_network,
    )

    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    scan_id = f'scout-{uuid.uuid4().hex[:8]}'
    warnings = list(batch.warnings) + list(outcome.warnings)

    return MarketScoutReport(
        scan_id=scan_id,
        scanned_at=now_utc,
        ai_engine_used=outcome.ai_engine_used,
        ai_engine_label=outcome.ai_engine_label,
        sources_summary=batch.sources_summary(),
        top_genre_insights=outcome.top_genre_insights,
        actionable_game_proposals=outcome.actionable_game_proposals,
        warnings=warnings,
    )
