import { ApiError, requestJson } from './client';
import type {
  AIProviderChoice,
  LatestScoutResponse,
  MarketScoutReport,
  ScoutMeta,
} from '../domain/scout';

function isMarketScoutReport(value: unknown): value is MarketScoutReport {
  if (typeof value !== 'object' || value === null) return false;
  const report = value as Record<string, unknown>;
  return typeof report.scan_id === 'string' &&
    typeof report.scanned_at === 'string' &&
    typeof report.ai_engine_used === 'string' &&
    typeof report.ai_engine_label === 'string' &&
    typeof report.sources_summary === 'object' &&
    report.sources_summary !== null &&
    Array.isArray(report.top_genre_insights) &&
    Array.isArray(report.actionable_game_proposals) &&
    Array.isArray(report.warnings);
}

function isScoutMeta(value: unknown): value is ScoutMeta {
  if (typeof value !== 'object' || value === null) return false;
  const meta = value as Record<string, unknown>;
  return typeof meta.configured_provider === 'string' &&
    typeof meta.ollama_base_url === 'string' &&
    typeof meta.ollama_model === 'string' &&
    typeof meta.api_configured === 'boolean';
}

export async function getLatestScoutReport(signal?: AbortSignal): Promise<LatestScoutResponse> {
  const body = await requestJson('/api/v1/scout/latest', { signal });
  if (typeof body !== 'object' || body === null || !('data' in body) || !('meta' in body)) {
    throw new ApiError('INVALID_RESPONSE', 'Piyasa araştırma yanıtı beklenen sözleşmeye uymuyor.');
  }
  const envelope = body as { data: unknown; meta: unknown };
  if ((envelope.data !== null && !isMarketScoutReport(envelope.data)) || !isScoutMeta(envelope.meta)) {
    throw new ApiError('INVALID_RESPONSE', 'Piyasa araştırma verisi doğrulanamadı.');
  }
  return {
    data: envelope.data,
    meta: envelope.meta,
  };
}

export async function runMarketScout(provider: AIProviderChoice = 'auto'): Promise<MarketScoutReport> {
  const body = await requestJson('/api/v1/scout/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider }),
  });
  if (typeof body !== 'object' || body === null || !('data' in body) || !isMarketScoutReport((body as { data: unknown }).data)) {
    throw new ApiError('INVALID_RESPONSE', 'AI piyasa taraması yanıtı doğrulanamadı.');
  }
  return (body as { data: MarketScoutReport }).data;
}
