import { ApiError, requestJson } from './client';
import type { Game, GamesResponse, PlatformFilter } from '../domain/game';

function isGame(value: unknown): value is Game {
  if (typeof value !== 'object' || value === null) return false;
  const game = value as Record<string, unknown>;
  return ['game_id', 'external_app_id', 'title', 'source_record_id'].every(key =>
    typeof game[key] === 'string' && (game[key] as string).trim().length > 0) &&
    (game.platform === 'android' || game.platform === 'ios') &&
    ['indie', 'small_team', 'unknown'].includes(String(game.developer_profile)) &&
    Array.isArray(game.normalized_genres) && game.normalized_genres.every(item => typeof item === 'string');
}

export async function listGames(platform: PlatformFilter, signal?: AbortSignal): Promise<GamesResponse> {
  const query = platform === 'all' ? '' : `?platform=${encodeURIComponent(platform)}`;
  const body = await requestJson(`/api/v1/games${query}`, { signal });
  if (typeof body !== 'object' || body === null || !('data' in body) || !('meta' in body) ||
      !Array.isArray(body.data) || !body.data.every(isGame) ||
      typeof body.meta !== 'object' || body.meta === null ||
      !('data_origin' in body.meta) || body.meta.data_origin !== 'synthetic_demo' ||
      !('demo_label' in body.meta) || typeof body.meta.demo_label !== 'string' ||
      !('count' in body.meta) || !Number.isInteger(body.meta.count) || body.meta.count !== body.data.length) {
    throw new ApiError('INVALID_RESPONSE', 'Oyun yanıtı beklenen demo veri sözleşmesine uymuyor.');
  }
  return body as GamesResponse;
}

export async function importGames(content: string): Promise<void> {
  await requestJson('/api/v1/imports', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: content,
  });
}
