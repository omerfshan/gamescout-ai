export type AIProviderChoice = 'auto' | 'ollama' | 'openai' | 'gemini';

export interface EvidenceQuote {
  source: 'app_store' | 'google_play' | 'reddit';
  source_label: string;
  subject: string;
  quote: string;
  rating: number | null;
}

export interface GenreDemandInsight {
  genre: string;
  demand_badge: string;
  summary: string;
  pain_points: string[];
  requested_mechanics: string[];
  signal_count: number;
}

export interface GameOpportunityProposal {
  opportunity_id: string;
  recommended_genre: string;
  concept_title: string;
  tagline: string;
  why_people_want_this: string;
  core_loop: string;
  target_audience: string;
  solved_complaints: string[];
  monetization_model: string;
  risks: string[];
  prototype_plan: string;
  evidence_quotes: EvidenceQuote[];
}

export interface MarketScoutReport {
  scan_id: string;
  scanned_at: string;
  ai_engine_used: string;
  ai_engine_label: string;
  sources_summary: {
    app_store_count: number;
    google_play_count: number;
    reddit_count: number;
    total_signals: number;
    live_sources_used: string[];
  };
  top_genre_insights: GenreDemandInsight[];
  actionable_game_proposals: GameOpportunityProposal[];
  warnings: string[];
}

export interface ScoutMeta {
  configured_provider: string;
  ollama_base_url: string;
  ollama_model: string;
  api_configured: boolean;
}

export interface LatestScoutResponse {
  data: MarketScoutReport | null;
  meta: ScoutMeta;
}
