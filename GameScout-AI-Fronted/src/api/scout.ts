import { ApiError, requestJson } from './client';
import type { AIProviderChoice, LatestScoutResponse, MarketScoutReport, ScoutMeta } from '../domain/scout';

type JsonObject = Record<string, unknown>;
const object = (value: unknown): value is JsonObject => typeof value === 'object' && value !== null && !Array.isArray(value);
const text = (value: unknown): value is string => typeof value === 'string';
const oneOf = (value: unknown, choices: readonly string[]): boolean => text(value) && choices.includes(value);
const strings = (value: unknown): value is string[] => Array.isArray(value) && value.every(text);
const count = (value: unknown): value is number => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
const optional = (record: JsonObject, key: string, check: (value: unknown) => boolean): boolean => record[key] === undefined || check(record[key]);
const nullableText = (value: unknown): boolean => value === null || text(value);
const safeUrl = (value: unknown): boolean => {
  if (value === null || value === undefined) return true;
  if (!text(value)) return false;
  try { return ['https:', 'http:'].includes(new URL(value).protocol); } catch { return false; }
};

function evidence(value: unknown): boolean {
  if (!object(value)) return false;
  return oneOf(value.source, ['app_store', 'google_play', 'reddit', 'community', 'web']) &&
    ['source_label', 'subject', 'quote'].every(key => text(value[key])) &&
    (value.rating === null || (typeof value.rating === 'number' && Number.isFinite(value.rating) && value.rating >= 1 && value.rating <= 5)) &&
    safeUrl(value.url) && ['evidence_id', 'original_text', 'language'].every(key => optional(value, key, text)) &&
    ['fetched_at', 'published_at', 'translation_text'].every(key => optional(value, key, nullableText)) &&
    optional(value, 'data_origin', v => v === 'live' || v === 'synthetic_demo') &&
    optional(value, 'signal_kind', v => oneOf(v, ['review', 'request', 'discussion', 'article']));
}

function proposal(value: unknown): boolean {
  if (!object(value)) return false;
  const requiredText = ['opportunity_id', 'recommended_genre', 'concept_title', 'tagline', 'why_people_want_this',
    'core_loop', 'target_audience', 'monetization_model', 'prototype_plan'];
  const optionalText = ['story_and_world', 'characters_and_npcs', 'player_actions', 'progression_and_rewards',
    'similar_games_and_differences', 'platform_fit', 'small_team_feasibility', 'ai_verdict', 'hypothesis_label'];
  return requiredText.every(key => text(value[key])) && optionalText.every(key => optional(value, key, text)) &&
    strings(value.solved_complaints) && strings(value.risks) &&
    ['unique_mechanics', 'retention_hooks', 'evidence_ids', 'need_ids', 'counter_evidence_ids'].every(key => optional(value, key, strings)) &&
    Array.isArray(value.evidence_quotes) && value.evidence_quotes.every(evidence) &&
    optional(value, 'early_experience', v => v === null || (object(v) && ['minute_5', 'minute_15', 'minute_30'].every(key => text(v[key]))));
}

function need(value: unknown): boolean {
  return object(value) && text(value.need_id) && text(value.statement) && strings(value.evidence_ids) &&
    strings(value.limitations) && strings(value.counter_evidence_ids);
}

export function isMarketScoutReport(value: unknown): value is MarketScoutReport {
  if (!object(value) || !object(value.sources_summary)) return false;
  const summary = value.sources_summary;
  const validInsights = Array.isArray(value.top_genre_insights) && value.top_genre_insights.every(item =>
    object(item) && ['genre', 'demand_badge', 'summary'].every(key => text(item[key])) &&
    strings(item.pain_points) && strings(item.requested_mechanics) && count(item.signal_count));
  return ['scan_id', 'scanned_at', 'ai_engine_used', 'ai_engine_label'].every(key => text(value[key])) &&
    ['app_store_count', 'google_play_count', 'reddit_count', 'total_signals'].every(key => count(summary[key])) &&
    strings(summary.live_sources_used) && ['community_count', 'web_count'].every(key => optional(summary, key, count)) &&
    optional(summary, 'source_statuses', v => object(v) && Object.values(v).every(text)) &&
    validInsights && Array.isArray(value.actionable_game_proposals) && value.actionable_game_proposals.every(proposal) &&
    strings(value.warnings) && optional(value, 'status', v => oneOf(v, ['completed', 'partial', 'insufficient_data', 'model_unavailable'])) &&
    optional(value, 'data_origin', v => oneOf(v, ['live', 'synthetic_demo', 'no_data'])) &&
    optional(value, 'player_needs', v => Array.isArray(v) && v.every(need)) && optional(value, 'model_metadata', object);
}

function isScoutMeta(value: unknown): value is ScoutMeta {
  return object(value) && text(value.configured_provider) && text(value.ollama_model) &&
    typeof value.api_configured === 'boolean' && optional(value, 'ollama_base_url', text);
}

export async function getLatestScoutReport(signal?: AbortSignal): Promise<LatestScoutResponse> {
  const body = await requestJson('/api/v1/scout/latest', { signal });
  if (!object(body) || (body.data !== null && !isMarketScoutReport(body.data)) || !isScoutMeta(body.meta)) {
    throw new ApiError('INVALID_RESPONSE', 'Piyasa araştırma raporunun alanları doğrulanamadı. Eksik veya eski raporu yeniden oluşturun.');
  }
  return { data: body.data, meta: body.meta };
}

export async function runMarketScout(provider: AIProviderChoice = 'ollama', genre: string = 'all'): Promise<MarketScoutReport> {
  const body = await requestJson('/api/v1/scout/runs', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ provider, genre }),
  });
  if (!object(body) || !isMarketScoutReport(body.data)) {
    throw new ApiError('INVALID_RESPONSE', 'AI araştırma raporunun alanları doğrulanamadı.');
  }
  return body.data;
}
