"""Deterministic Discovery use case; does not own Laravel persistence."""
from collections.abc import Sequence
from gamescout_ai.domain.models import DiscoveryResult, Game, Scope, ValidationError


def discover(games: Sequence[Game], scope: Scope) -> DiscoveryResult:
    unique: dict[tuple[str, str], Game] = {}
    for game in games:
        key = (game.platform, game.external_app_id)
        previous = unique.get(key)
        if previous is not None and previous != game:
            raise ValidationError('CONFLICTING_DUPLICATE', 'Aynı platform ve uygulama kimliği çelişkili kayıtlar içeriyor.')
        unique[key] = game
    matched = sorted((game for game in unique.values()
                      if game.platform == scope.platform
                      and (scope.genre is None or scope.genre in game.normalized_genres)
                      and (scope.developer_profile is None or game.developer_profile == scope.developer_profile)),
                     key=lambda game: (game.platform, game.external_app_id, game.game_id))
    returned = tuple(matched[:scope.max_games])
    warnings = ['Sentetik demo; gelir, indirme veya pazar başarısı çıkarılamaz.']
    if len(unique) < len(games):
        warnings.append('Aynı içerikli yinelenen oyunlar tekilleştirildi.')
    if len(matched) > scope.max_games:
        warnings.append('Sonuç yapılandırılmış oyun sınırı nedeniyle kesildi.')
    if not returned:
        warnings.append('Seçilen kapsamda oyun bulunamadı.')
    return DiscoveryResult(returned, len(games), len(unique), len(matched), len(returned),
                           'completed' if returned else 'insufficient_data', tuple(warnings))
