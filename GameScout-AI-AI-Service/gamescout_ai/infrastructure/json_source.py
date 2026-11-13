"""Bounded local JSON ingestion. No HTTP, database or model access."""
import json
from pathlib import Path
from typing import Any
from gamescout_ai.domain.models import Game, ValidationError

MAX_FILE_BYTES = 1024 * 1024
MAX_INPUT_GAMES = 1000


def required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError('INVALID_GAME', f'{field} boş olmayan metin olmalıdır.')
    return value.strip()


def parse_game(value: Any, index: int) -> Game:
    if not isinstance(value, dict):
        raise ValidationError('INVALID_GAME', f'games[{index}] nesne olmalıdır.')
    def text(name: str) -> str:
        return required_text(value.get(name), f'games[{index}].{name}')
    platform = text('platform')
    profile = text('developer_profile')
    if platform not in ('android', 'ios'):
        raise ValidationError('INVALID_GAME', f'games[{index}].platform geçersiz.')
    if profile not in ('indie', 'small_team', 'unknown'):
        raise ValidationError('INVALID_GAME', f'games[{index}].developer_profile geçersiz.')
    genres = value.get('normalized_genres')
    if not isinstance(genres, list):
        raise ValidationError('INVALID_GAME', f'games[{index}].normalized_genres liste olmalıdır.')
    normalized = tuple(required_text(g, f'games[{index}].normalized_genres') for g in genres)
    return Game(text('game_id'), platform, text('external_app_id'), text('title'), profile,
                text('source_record_id'), normalized)


def parse_payload(payload: Any) -> tuple[Game, ...]:
    if not isinstance(payload, dict):
        raise ValidationError('INVALID_PAYLOAD', 'JSON kökü nesne olmalıdır.')
    if payload.get('schema_version') != '1.0.0':
        raise ValidationError('UNSUPPORTED_SCHEMA', 'schema_version 1.0.0 olmalıdır.')
    if payload.get('data_origin') != 'synthetic_demo':
        raise ValidationError('UNSUPPORTED_ORIGIN', 'Bu sürüm yalnızca synthetic_demo verisini kabul eder.')
    games = payload.get('games')
    if not isinstance(games, list):
        raise ValidationError('INVALID_PAYLOAD', 'games liste olmalıdır.')
    if len(games) > MAX_INPUT_GAMES:
        raise ValidationError('TOO_MANY_GAMES', 'En fazla 1000 girdi oyunu kabul edilir.')
    # Additional fixture fields are intentionally ignored; known fields remain strict.
    return tuple(parse_game(game, i) for i, game in enumerate(games))


def load_file(path: str | Path) -> tuple[Game, ...]:
    try:
        with Path(path).open('rb') as stream:
            raw = stream.read(MAX_FILE_BYTES + 1)
    except OSError as error:
        raise ValidationError('FILE_UNAVAILABLE', 'Girdi dosyası okunamadı.') from error
    if len(raw) > MAX_FILE_BYTES:
        raise ValidationError('FILE_TOO_LARGE', 'Girdi dosyası en fazla 1 MiB olabilir.')
    try:
        payload = json.loads(raw.decode('utf-8'), parse_constant=lambda value: reject_constant())
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValidationError('INVALID_JSON', 'Girdi geçerli UTF-8 JSON olmalıdır.') from error
    return parse_payload(payload)


def reject_constant() -> None:
    raise ValidationError('INVALID_JSON', 'JSON sonlu sayılar içermelidir.')
