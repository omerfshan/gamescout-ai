"""Domain models and SOLID port contracts for the AI Game Opportunity Researcher (Scout)."""
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

SignalSource = Literal['app_store', 'google_play', 'reddit', 'community', 'web']


@dataclass(frozen=True)
class EvidenceQuote:
    source: SignalSource
    source_label: str
    subject: str
    quote: str
    rating: int | None = None
    url: str | None = None
    evidence_id: str = ''
    original_text: str = ''
    fetched_at: str | None = None
    published_at: str | None = None
    signal_kind: str = 'review'
    data_origin: str = 'live'
    language: str = 'unknown'
    translation_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PlayerNeed:
    need_id: str
    statement: str
    evidence_ids: list[str]
    counter_evidence_ids: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

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
class EarlyPlayerExperience:
    minute_5: str
    minute_15: str
    minute_30: str

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
    # Deep Creative Game Concept fields
    story_and_world: str = ''
    characters_and_npcs: str = ''
    player_actions: str = ''
    unique_mechanics: list[str] = field(default_factory=list)
    early_experience: EarlyPlayerExperience | None = None
    retention_hooks: list[str] = field(default_factory=list)
    progression_and_rewards: str = ''
    similar_games_and_differences: str = ''
    platform_fit: str = ''
    small_team_feasibility: str = ''
    ai_verdict: str = ''
    evidence_quotes: list[EvidenceQuote] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    need_ids: list[str] = field(default_factory=list)
    counter_evidence_ids: list[str] = field(default_factory=list)
    hypothesis_label: str = 'unvalidated_design_hypothesis'

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
            'story_and_world': self.story_and_world,
            'characters_and_npcs': self.characters_and_npcs,
            'player_actions': self.player_actions,
            'unique_mechanics': list(self.unique_mechanics),
            'early_experience': self.early_experience.to_dict() if self.early_experience else None,
            'retention_hooks': list(self.retention_hooks),
            'progression_and_rewards': self.progression_and_rewards,
            'similar_games_and_differences': self.similar_games_and_differences,
            'platform_fit': self.platform_fit,
            'small_team_feasibility': self.small_team_feasibility,
            'ai_verdict': self.ai_verdict,
            'evidence_quotes': [quote.to_dict() for quote in self.evidence_quotes],
            'evidence_ids': list(self.evidence_ids),
            'need_ids': list(self.need_ids),
            'counter_evidence_ids': list(self.counter_evidence_ids),
            'hypothesis_label': self.hypothesis_label,
        }


@dataclass(frozen=True)
class CollectedSignalBatch:
    signals: list[EvidenceQuote]
    live_sources_used: list[str]
    warnings: list[str] = field(default_factory=list)
    data_origin: str = 'no_data'
    source_statuses: dict[str, str] = field(default_factory=dict)

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
            'community_count': sum(item.source == 'community' for item in self.signals),
            'web_count': sum(item.source == 'web' for item in self.signals),
            'data_origin': self.data_origin,
            'source_statuses': dict(self.source_statuses),
            'signal_kind_counts': {kind: sum(item.signal_kind == kind for item in self.signals)
                                   for kind in ('review', 'request', 'discussion', 'article')},
        }


@dataclass(frozen=True)
class SynthesisOutcome:
    ai_engine_used: str
    ai_engine_label: str
    top_genre_insights: list[GenreDemandInsight]
    actionable_game_proposals: list[GameOpportunityProposal]
    warnings: list[str] = field(default_factory=list)
    status: str = 'insufficient_data'
    player_needs: list[PlayerNeed] = field(default_factory=list)
    model_metadata: dict[str, Any] = field(default_factory=dict)
    data_origin: str = 'no_data'


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
    status: str = 'insufficient_data'
    player_needs: list[PlayerNeed] = field(default_factory=list)
    model_metadata: dict[str, Any] = field(default_factory=dict)
    data_origin: str = 'no_data'
    evidence_snapshot: list[EvidenceQuote] = field(default_factory=list)

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
            'status': self.status,
            'data_origin': self.data_origin,
            'player_needs': [need.to_dict() for need in self.player_needs],
            'model_metadata': dict(self.model_metadata),
            'evidence_snapshot': [item.to_dict() for item in self.evidence_snapshot],
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
        genre: str = 'all',
    ) -> SynthesisOutcome:
        raise NotImplementedError


class ModelClientPort(ABC):
    """One bounded structured model call; adapters own transport only."""
    @abstractmethod
    def complete(self, system_prompt: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
