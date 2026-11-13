"""Domain models and SOLID port contracts for the AI Game Opportunity Researcher (Scout)."""
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

SignalSource = Literal['app_store', 'google_play', 'reddit']


@dataclass(frozen=True)
class EvidenceQuote:
    source: SignalSource
    source_label: str
    subject: str
    quote: str
    rating: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GenreDemandInsight:
    genre: str
    demand_badge: str
    summary: str
    pain_points: list[str]
    requested_mechanics: list[str]
    signal_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GameOpportunityProposal:
    opportunity_id: str
    recommended_genre: str
    concept_title: str
    tagline: str
    why_people_want_this: str
    core_loop: str
    target_audience: str
    solved_complaints: list[str]
    monetization_model: str
    risks: list[str]
    prototype_plan: str
    evidence_quotes: list[EvidenceQuote] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'opportunity_id': self.opportunity_id,
            'recommended_genre': self.recommended_genre,
            'concept_title': self.concept_title,
            'tagline': self.tagline,
            'why_people_want_this': self.why_people_want_this,
            'core_loop': self.core_loop,
            'target_audience': self.target_audience,
            'solved_complaints': list(self.solved_complaints),
            'monetization_model': self.monetization_model,
            'risks': list(self.risks),
            'prototype_plan': self.prototype_plan,
            'evidence_quotes': [quote.to_dict() for quote in self.evidence_quotes],
        }


@dataclass(frozen=True)
class CollectedSignalBatch:
    signals: list[EvidenceQuote]
    live_sources_used: list[str]
    warnings: list[str] = field(default_factory=list)

    def sources_summary(self) -> dict[str, Any]:
        app_store_count = sum(1 for item in self.signals if item.source == 'app_store')
        google_play_count = sum(1 for item in self.signals if item.source == 'google_play')
        reddit_count = sum(1 for item in self.signals if item.source == 'reddit')
        return {
            'app_store_count': app_store_count,
            'google_play_count': google_play_count,
            'reddit_count': reddit_count,
            'total_signals': len(self.signals),
            'live_sources_used': list(self.live_sources_used),
        }


@dataclass(frozen=True)
class SynthesisOutcome:
    ai_engine_used: str
    ai_engine_label: str
    top_genre_insights: list[GenreDemandInsight]
    actionable_game_proposals: list[GameOpportunityProposal]
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MarketScoutReport:
    scan_id: str
    scanned_at: str
    ai_engine_used: str
    ai_engine_label: str
    sources_summary: dict[str, Any]
    top_genre_insights: list[GenreDemandInsight]
    actionable_game_proposals: list[GameOpportunityProposal]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'scan_id': self.scan_id,
            'scanned_at': self.scanned_at,
            'ai_engine_used': self.ai_engine_used,
            'ai_engine_label': self.ai_engine_label,
            'sources_summary': dict(self.sources_summary),
            'top_genre_insights': [item.to_dict() for item in self.top_genre_insights],
            'actionable_game_proposals': [item.to_dict() for item in self.actionable_game_proposals],
            'warnings': list(self.warnings),
        }


class SignalCollectorPort(ABC):
    """Port interface for collecting market signals from App Store, Google Play, and Reddit."""

    @abstractmethod
    def collect_signals(self, allow_network: bool = True) -> CollectedSignalBatch:
        raise NotImplementedError


class OpportunitySynthesizerPort(ABC):
    """Port interface for synthesizing player demand and actionable game proposals via AI/LLM."""

    @abstractmethod
    def synthesize(
        self,
        batch: CollectedSignalBatch,
        provider: str = 'auto',
        allow_network: bool = True,
    ) -> SynthesisOutcome:
        raise NotImplementedError
