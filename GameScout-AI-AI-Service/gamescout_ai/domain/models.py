"""Framework-independent Discovery data and errors."""
from dataclasses import asdict, dataclass
from typing import Literal

Platform = Literal['android', 'ios']
DeveloperProfile = Literal['indie', 'small_team', 'unknown']


class ValidationError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class Game:
    game_id: str
    platform: Platform
    external_app_id: str
    title: str
    developer_profile: DeveloperProfile
    source_record_id: str
    normalized_genres: tuple[str, ...]


@dataclass(frozen=True)
class Scope:
    platform: Platform
    max_games: int = 10
    genre: str | None = None
    developer_profile: DeveloperProfile | None = None

    def __post_init__(self) -> None:
        if self.platform not in ('android', 'ios'):
            raise ValidationError('INVALID_SCOPE', 'Platform android veya ios olmalıdır.')
        if type(self.max_games) is not int or not 1 <= self.max_games <= 20:
            raise ValidationError('INVALID_SCOPE', 'max_games 1–20 arasında tam sayı olmalıdır.')
        if self.genre is not None and (not isinstance(self.genre, str) or not self.genre.strip()):
            raise ValidationError('INVALID_SCOPE', 'Tür boş olmayan metin olmalıdır.')
        if self.developer_profile is not None and self.developer_profile not in ('indie', 'small_team', 'unknown'):
            raise ValidationError('INVALID_SCOPE', 'Geliştirici profili geçersiz.')


@dataclass(frozen=True)
class DiscoveryResult:
    games: tuple[Game, ...]
    input_count: int
    deduplicated_count: int
    matched_count: int
    returned_count: int
    status: Literal['completed', 'insufficient_data']
    warnings: tuple[str, ...]
    schema_version: str = '1.0.0'
    data_origin: str = 'synthetic_demo'
    demo_label: str = 'Sentetik demo — gerçek pazar verisi değildir.'

    def to_dict(self) -> dict:
        return asdict(self)
