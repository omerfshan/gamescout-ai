export type AIProviderChoice = 'auto' | 'ollama' | 'openai' | 'gemini';

export type MobileGameCategory =
  | 'all'
  | 'action'
  | 'rpg'
  | 'strategy'
  | 'roguelike'
  | 'simulation'
  | 'puzzle'
  | 'survival'
  | 'casual'
  | 'racing_sports'
  | 'adventure';

export interface CategoryOption {
  key: MobileGameCategory;
  label: string;
}

export const OFFICIAL_MOBILE_CATEGORIES: CategoryOption[] = [
  { key: 'all', label: 'Tüm Kategoriler (Otomatik Keşif)' },
  { key: 'action', label: 'Aksiyon (Action & Shooter)' },
  { key: 'rpg', label: 'Rol Yapma (RPG & Lonca)' },
  { key: 'strategy', label: 'Strateji & Kule Savunması (Strategy & Tower Defense)' },
  { key: 'roguelike', label: 'Roguelike & Deste İnşası (Card & Deckbuilder)' },
  { key: 'simulation', label: 'Simülasyon & Otomasyon (Cozy & Management)' },
  { key: 'puzzle', label: 'Bulmaca & Zeka (Puzzle & Tactics)' },
  { key: 'survival', label: 'Hayatta Kalma & Arena (Survival & Roguelite)' },
  { key: 'casual', label: 'Basit Eğlence & Boşta (Casual & Idle)' },
  { key: 'racing_sports', label: 'Yarış & Spor (Racing & Sports)' },
  { key: 'adventure', label: 'Macera & Hikaye (Adventure & Narrative)' },
];

export interface EvidenceQuote {
  source: 'app_store' | 'google_play' | 'reddit' | 'community' | 'web';
  source_label: string;
  subject: string;
  quote: string;
  rating: number | null;
  url?: string | null;
  evidence_id?: string;
  original_text?: string;
  fetched_at?: string | null;
  published_at?: string | null;
  signal_kind?: 'review' | 'request' | 'discussion' | 'article';
  data_origin?: 'live' | 'synthetic_demo';
  language?: string;
  translation_text?: string | null;
}

export interface GenreDemandInsight {
  genre: string;
  demand_badge: string;
  summary: string;
  pain_points: string[];
  requested_mechanics: string[];
  signal_count: number;
}

export interface EarlyPlayerExperience {
  minute_5: string;
  minute_15: string;
  minute_30: string;
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
  // Deep Creative Game Concept fields
  story_and_world?: string;
  characters_and_npcs?: string;
  player_actions?: string;
  unique_mechanics?: string[];
  early_experience?: EarlyPlayerExperience | null;
  retention_hooks?: string[];
  progression_and_rewards?: string;
  similar_games_and_differences?: string;
  platform_fit?: string;
  small_team_feasibility?: string;
  ai_verdict?: string;
  evidence_quotes: EvidenceQuote[];
  evidence_ids?: string[];
  need_ids?: string[];
  counter_evidence_ids?: string[];
  hypothesis_label?: string;
}

export interface PlayerNeed {
  need_id: string;
  statement: string;
  evidence_ids: string[];
  limitations: string[];
  counter_evidence_ids?: string[];
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
    source_statuses?: Record<string, string>;
    data_origin?: string;
    community_count?: number;
    web_count?: number;
  };
  top_genre_insights: GenreDemandInsight[];
  actionable_game_proposals: GameOpportunityProposal[];
  warnings: string[];
  status?: 'completed' | 'partial' | 'insufficient_data' | 'model_unavailable';
  data_origin?: 'live' | 'synthetic_demo' | 'no_data';
  player_needs?: PlayerNeed[];
  model_metadata?: Record<string, unknown>;
}

export interface ScoutMeta {
  configured_provider: string;
  ollama_base_url?: string;
  ollama_model: string;
  api_configured: boolean;
}

export interface LatestScoutResponse {
  data: MarketScoutReport | null;
  meta: ScoutMeta;
}
