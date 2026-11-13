import type { Game } from '../../domain/game';

const profiles = { indie: 'Bağımsız geliştirici', small_team: 'Küçük ekip', unknown: 'Geliştirici profili bilinmiyor' };

export function GameCard({ game }: { game: Game }) {
  return <article className="game-card">
    <div className="game-card__top"><span className="platform">{game.platform === 'android' ? 'Android' : 'iOS'}</span></div>
    <h3>{game.title}</h3>
    <p>{profiles[game.developer_profile]}</p>
    <ul className="tags" aria-label="Oyun türleri">{game.normalized_genres.map(genre => <li key={genre}>{genre.replaceAll('_', ' ')}</li>)}</ul>
    <dl><dt>Uygulama kimliği</dt><dd>{game.external_app_id}</dd><dt>Kanıt kaydı</dt><dd>{game.source_record_id}</dd></dl>
  </article>;
}
