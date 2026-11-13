import { useEffect, useState } from 'react';
import { getLatestScoutReport, runMarketScout } from '../../api/scout';
import type { AIProviderChoice, MarketScoutReport, ScoutMeta } from '../../domain/scout';
import { OFFICIAL_MOBILE_CATEGORIES } from '../../domain/scout';
import { StatusMessage } from '../../components/StatusMessage';

function formatScanTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    if (Number.isNaN(date.getTime())) return isoString;
    return date.toLocaleString('tr-TR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
}

function renderStars(rating: number | null): string {
  if (rating === null) return '';
  const clamped = Math.max(1, Math.min(5, Math.round(rating)));
  return `${'★'.repeat(clamped)}${'☆'.repeat(5 - clamped)} (${rating}/5)`;
}

export function OpportunityScoutPanel() {
  const [provider, setProvider] = useState<AIProviderChoice>('ollama');
  const [genre, setGenre] = useState<string>('all');
  const [report, setReport] = useState<MarketScoutReport | null>(null);
  const [meta, setMeta] = useState<ScoutMeta | null>(null);
  const [loadingLatest, setLoadingLatest] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    setLoadingLatest(true);
    getLatestScoutReport(controller.signal)
      .then(result => {
        if (!controller.signal.aborted) {
          setReport(result.data);
          setMeta(result.meta);
        }
      })
      .catch(failure => {
        if (!controller.signal.aborted) {
          setError(failure instanceof Error ? failure.message : 'Önceki piyasa araştırması yüklenemedi.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoadingLatest(false);
        }
      });
    return () => controller.abort();
  }, []);

  async function handleScan() {
    setError('');
    setScanning(true);
    try {
      const freshReport = await runMarketScout(provider, genre);
      setReport(freshReport);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'AI oyun konsepti araştırması tamamlanamadı.');
    } finally {
      setScanning(false);
    }
  }

  return <section className="scout-dashboard" aria-labelledby="command-center-title">
    <div className="command-center-hero">
      <div className="command-center-hero__left">
        <div className="command-center-badges">
          <span className="cc-badge cc-badge--glow">
            OTONOM AI OYUN KONSEPT VE FIRSAT DİREKTÖRÜ
          </span>
          {meta && (
            <span className="cc-badge cc-badge--engine">
              ⚡ Yapılandırılan Model: {meta.configured_provider.toUpperCase()} ({meta.ollama_model})
            </span>
          )}
        </div>

        <h1 id="command-center-title">
          Oyuncuların Hayallerinden Yeni Mobil Oyunlar.<br />
          <span>Oyuncu isteklerinden kanıta bağlı oyun hipotezleri.</span>
        </h1>
        <p className="command-center-lead">
          Uygulamanın modeli; erişilebilen oyuncu isteklerini, öneri arayışlarını, tartışmaları ve yorumları inceler. Desteklenen ihtiyaçlardan <strong>denenebilir mobil oyun konseptleri</strong> üretir. Veri yetersizse veya model çalışmıyorsa fikir uydurmaz.
        </p>
      </div>

      <div className="command-center-hero__right">
        <div className="command-control-box">
          <label className="cc-select-label">
            <span>Hedef Oyun Türü</span>
            <select
              value={genre}
              onChange={event => setGenre(event.target.value)}
              disabled={scanning}
            >
              {OFFICIAL_MOBILE_CATEGORIES.map(category => (
                <option key={category.key} value={category.key}>
                  {category.label}
                </option>
              ))}
            </select>
          </label>

          <label className="cc-select-label">
            <span>Yapay Zekâ Motoru</span>
            <select
              value={provider}
              onChange={event => setProvider(event.target.value as AIProviderChoice)}
              disabled={scanning}
            >
              <option value="ollama">Yerel Ollama (yapılandırılan model)</option>
              <option value="auto">Otomatik (Yerel Ollama / API Öncelikli)</option>
              <option value="gemini">Harici API (Google Gemini)</option>
              <option value="openai">Harici API (OpenAI)</option>
            </select>
          </label>

          <button
            type="button"
            className="cc-scan-btn"
            onClick={handleScan}
            disabled={scanning}
          >
            <span>
              {scanning
                ? 'Oyuncu İstekleri Taranıyor ve Oyunlar Tasarlanıyor…'
                : 'Oyuncu İhtiyaçlarını Araştır'}
            </span>
          </button>
        </div>
      </div>

      {scanning && (
        <div className="live-radar-panel" role="status" aria-live="polite">
          <div className="live-radar-header">
            <div className="radar-spinner" aria-hidden="true" />
            <div>
              <strong>Oyun Fırsatı Araştırması Çalışıyor</strong>
              <span>Erişilebilen kaynaklar toplanıyor; uygulamanın modeli ihtiyaçları çıkarıp kaynak destekli konsept hipotezleri oluşturuyor…</span>
            </div>
          </div>
        </div>
      )}
    </div>

    {error && <StatusMessage kind="error" message={error} />}

    {loadingLatest && !report && (
      <div className="session-loader" role="status">
        <div className="radar-spinner" aria-hidden="true" />
        <p>Son oyun konsept raporu yükleniyor…</p>
      </div>
    )}

    {!loadingLatest && !report && !scanning && (
      <div className="empty-intelligence-card">
        <div className="empty-intelligence-icon" aria-hidden="true">✦</div>
        <h2>Henüz Oyun Konsept Araştırması Başlatılmadı</h2>
        <p>
          Yukarıdaki <strong>“Oyuncu İhtiyaçlarını Araştır”</strong> butonuna tıkladığınızda;
          etkin kaynaklardaki oyuncu istekleri ve tartışmaları toplanır. Model yalnızca yeterli kaynak desteği bulduğunda konsept hipotezleri üretir.
        </p>
      </div>
    )}

    {report && (
      <div className="scout-results-container">
        <div className="scout-notice-banner" role="status">
          <p><strong>Veri kökeni:</strong> {report.data_origin === 'synthetic_demo' ? 'Sentetik demo — gerçek pazar araştırması değildir.' : report.data_origin === 'live' ? 'Canlı kaynak kayıtları — örneklem bütün pazarı temsil etmez.' : report.data_origin === 'no_data' ? 'Kullanılabilir kaynak verisi yok.' : 'Eski/belirsiz kayıt — veri kökeni doğrulanmadı.'}</p>
          <p><strong>Durum:</strong> {report.status === 'model_unavailable' ? 'Model kullanılamadı; otomatik yedek oyun fikri üretilmedi.' : report.status === 'insufficient_data' ? 'Kaynak veya ihtiyaç desteği yetersiz; fikir üretimi sınırlandırıldı.' : report.status === 'partial' ? 'Kısmi sonuç; sınırlılıkları inceleyin.' : report.status === 'completed' ? 'İşlem tamamlandı; konseptler hâlâ doğrulanmamış hipotezlerdir.' : 'Eski rapor; yeni doğrulama akışıyla yeniden araştırın.'}</p>
          {typeof report.model_metadata?.model === 'string' && <p><strong>Kullanılan model:</strong> {report.model_metadata.model}</p>}
          <p>Kaynak kimliği eşleşmesi, metnin bütün iddiaları desteklediğini garanti etmez. İnsan incelemesi gerekir.</p>
          {report.sources_summary.source_statuses && <ul>{Object.entries(report.sources_summary.source_statuses).map(([source, status]) => <li key={source}>{source}: {status}</li>)}</ul>}
        </div>
        <div className="stats-bar-grid" role="region" aria-label="Tarama ve kaynak istatistikleri">
          <div className="stat-card stat-card--blue">
            <div className="stat-card__top">
              <span className="stat-card__label">APPLE APP STORE</span>
              <span className="stat-card__icon" aria-hidden="true"></span>
            </div>
            <strong className="stat-card__value">{report.sources_summary.app_store_count}</strong>
            <span className="stat-card__sub">Toplanan Kaynak Kaydı</span>
          </div>

          <div className="stat-card stat-card--green">
            <div className="stat-card__top">
              <span className="stat-card__label">GOOGLE PLAY</span>
              <span className="stat-card__icon" aria-hidden="true">▶</span>
            </div>
            <strong className="stat-card__value">{report.sources_summary.google_play_count}</strong>
            <span className="stat-card__sub">Toplanan Kaynak Kaydı</span>
          </div>

          <div className="stat-card stat-card--orange">
            <div className="stat-card__top">
              <span className="stat-card__label">TOPLULUK VE WEB</span>
              <span className="stat-card__icon" aria-hidden="true">◉</span>
            </div>
            <strong className="stat-card__value">{report.sources_summary.reddit_count + (report.sources_summary.community_count ?? 0) + (report.sources_summary.web_count ?? 0)}</strong>
            <span className="stat-card__sub">İncelenen Topluluk Tartışması</span>
          </div>

          <div className="stat-card stat-card--indigo">
            <div className="stat-card__top">
              <span className="stat-card__label">TOPLANAN SİNYALLER</span>
              <span className="stat-card__icon" aria-hidden="true">∑</span>
            </div>
            <strong className="stat-card__value">{report.sources_summary.total_signals}</strong>
            <span className="stat-card__sub">Kaynak kaydı; doğrulanmış pazar talebi değildir</span>
          </div>

          <div className="stat-card stat-card--emerald">
            <div className="stat-card__top">
              <span className="stat-card__label">AKTİF AI DİREKTÖRÜ</span>
              <span className="stat-card__icon" aria-hidden="true">⚡</span>
            </div>
            <strong className="stat-card__value stat-card__value--engine">{report.ai_engine_label}</strong>
            <span className="stat-card__sub">Araştırma Tarihi: {formatScanTime(report.scanned_at)}</span>
          </div>
        </div>

        {report.warnings.length > 0 && (
          <div className="scout-notice-banner">
            {report.warnings.map((warning, idx) => (
              <p key={idx}>ℹ️ {warning}</p>
            ))}
          </div>
        )}

        {report.player_needs && report.player_needs.length > 0 && <section className="intelligence-section" aria-labelledby="needs-heading">
          <div className="intelligence-section__header"><h2 id="needs-heading">Modelin Kaynaklardan Çıkardığı Oyuncu İhtiyaçları</h2></div>
          <div className="pros-risks-grid">{report.player_needs.map(need => <article key={need.need_id} className="pros-box">
            <h3>{need.statement}</h3>
            <p>İhtiyaç: {need.need_id} · Destekleyen kaynaklar: {need.evidence_ids.join(', ')}</p>
            {need.counter_evidence_ids && need.counter_evidence_ids.length > 0 && <p>Karşı kaynaklar: {need.counter_evidence_ids.join(', ')}</p>}
            <ul>{need.limitations.map((item, index) => <li key={index}>{item}</li>)}</ul>
          </article>)}</div>
        </section>}
        {report.actionable_game_proposals.length === 0 && <div className="empty-intelligence-card"><h2>Konsept hipotezi üretilmedi</h2><p>Model ve kaynak durumunu kontrol edin. Sistem eksik sonuçları hazır oyun fikirleriyle doldurmaz.</p></div>}
        <section className="intelligence-section" aria-labelledby="proposals-heading">
          <div className="intelligence-section__header">
            <div>
              <span className="section-eyebrow">MODELİN ÜRETTİĞİ MOBİL OYUN HİPOTEZLERİ</span>
              <h2 id="proposals-heading">“Şu Oyun Denenebilir” — Konsept Hipotezleri ({report.actionable_game_proposals.length})</h2>
            </div>
          </div>

          <div className="pitch-deck-list">
            {report.actionable_game_proposals.map((proposal, index) => (
              <article key={proposal.opportunity_id} className="pitch-card">
                <div className="pitch-card__top">
                  <div className="pitch-card__title-group">
                    <div className="pitch-card__badges">
                      <span className="rank-badge">Hipotez #{index + 1} · Deneyle doğrulanmalı</span>
                      <span className="genre-pill">{proposal.recommended_genre}</span>
                      <span className="monetization-pill">💎 {proposal.monetization_model}</span>
                    </div>
                    <h3 className="pitch-card__title">{proposal.concept_title}</h3>
                    <p className="pitch-card__subtitle">{proposal.tagline}</p>
                  </div>
                </div>

                {/* 1. Neden İsteniyor ve Dünya/Hikaye */}
                <div className="concept-deep-row">
                  <div className="concept-deep-box concept-deep-box--highlight">
                    <div className="concept-box-title">
                      <span className="box-icon" aria-hidden="true">🎯</span>
                      <h4>Oyuncular Bu Oyunu Neden İsteyebilir? (Deneyim İhtiyacı)</h4>
                    </div>
                    <p>{proposal.why_people_want_this}</p>
                  </div>

                  {proposal.story_and_world && (
                    <div className="concept-deep-box">
                      <div className="concept-box-title">
                        <span className="box-icon" aria-hidden="true">📜</span>
                        <h4>Oyunun Hikâyesi ve Dünyası</h4>
                      </div>
                      <p>{proposal.story_and_world}</p>
                    </div>
                  )}
                </div>

                {/* 2. Karakterler & Oyuncu Eylemleri */}
                {(proposal.characters_and_npcs || proposal.player_actions) && (
                  <div className="concept-deep-row">
                    {proposal.characters_and_npcs && (
                      <div className="concept-deep-box">
                        <div className="concept-box-title">
                          <span className="box-icon" aria-hidden="true">👤</span>
                          <h4>Ana Karakterler ve NPC'ler</h4>
                        </div>
                        <p>{proposal.characters_and_npcs}</p>
                      </div>
                    )}
                    {proposal.player_actions && (
                      <div className="concept-deep-box">
                        <div className="concept-box-title">
                          <span className="box-icon" aria-hidden="true">🎮</span>
                          <h4>Oyuncunun Oyunda Neler Yapacağı (Anbean Aksiyon)</h4>
                        </div>
                        <p>{proposal.player_actions}</p>
                      </div>
                    )}
                  </div>
                )}

                {/* 3. Özgün Mekanikler & Temel Döngü */}
                <div className="strategic-plan-grid">
                  <div className="strategy-box">
                    <div className="strategy-box__header">
                      <span className="strategy-icon" aria-hidden="true">✨</span>
                      <h4>Özgün Oynanış Mekanikleri</h4>
                    </div>
                    {proposal.unique_mechanics && proposal.unique_mechanics.length > 0 ? (
                      <ul className="concept-bullet-list">
                        {proposal.unique_mechanics.map((mech, mIdx) => (
                          <li key={mIdx}>{mech}</li>
                        ))}
                      </ul>
                    ) : (
                      <p>Model bu alanı belirtmedi.</p>
                    )}
                  </div>

                  <div className="strategy-box">
                    <div className="strategy-box__header">
                      <span className="strategy-icon" aria-hidden="true">🔄</span>
                      <h4>Temel Oynanış Döngüsü (Core Loop)</h4>
                    </div>
                    <p>{proposal.core_loop}</p>
                  </div>

                  <div className="strategy-box">
                    <div className="strategy-box__header">
                      <span className="strategy-icon" aria-hidden="true">👥</span>
                      <h4>Hedef Oyuncu Kitlesi</h4>
                    </div>
                    <p>{proposal.target_audience}</p>
                  </div>

                  <div className="strategy-box">
                    <div className="strategy-box__header">
                      <span className="strategy-icon" aria-hidden="true">📱</span>
                      <h4>Android/iOS Uygunluğu &amp; Küçük Ekip</h4>
                    </div>
                    <p>
                      <strong>Mobil Ergonomi:</strong> {proposal.platform_fit || 'Mobil uygunluğu değerlendirilmedi.'}<br />
                      <strong>Geliştirilebilirlik:</strong> {proposal.small_team_feasibility || 'Ekip ve kapsam değerlendirmesi yok.'}
                    </p>
                  </div>
                </div>

                {/* 4. İlk 5, 15 ve 30 Dakikalık Deneyim */}
                {proposal.early_experience && (
                  <div className="early-experience-card">
                    <h4>⏱ İlk Oyun Deneyimi Zaman Çizelgesi</h4>
                    <div className="experience-timeline-grid">
                      <div className="exp-step">
                        <span className="exp-badge">0 - 5. Dakika</span>
                        <p>{proposal.early_experience.minute_5}</p>
                      </div>
                      <div className="exp-step">
                        <span className="exp-badge">5 - 15. Dakika</span>
                        <p>{proposal.early_experience.minute_15}</p>
                      </div>
                      <div className="exp-step">
                        <span className="exp-badge">15 - 30. Dakika</span>
                        <p>{proposal.early_experience.minute_30}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* 5. Geri Getiren Özellikler, İlerleme & Benzer Oyunlar */}
                <div className="deep-insights-trio">
                  {proposal.retention_hooks && proposal.retention_hooks.length > 0 && (
                    <div className="trio-box">
                      <h5>🧲 Oyuncuyu Tekrar Getiren Özellikler</h5>
                      <ul>
                        {proposal.retention_hooks.map((hook, hIdx) => (
                          <li key={hIdx}>{hook}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {proposal.progression_and_rewards && (
                    <div className="trio-box">
                      <h5>📈 İlerleme ve Ödül Sistemi</h5>
                      <p>{proposal.progression_and_rewards}</p>
                    </div>
                  )}

                  {proposal.similar_games_and_differences && (
                    <div className="trio-box">
                      <h5>⚔ Benzer Oyunlar ve Farklılıkları</h5>
                      <p>{proposal.similar_games_and_differences}</p>
                    </div>
                  )}
                </div>

                {/* 6. Çözülen Şikayetler & Riskler */}
                <div className="pros-risks-grid">
                  <div className="pros-box">
                    <h4>✓ Karşılanan Deneyim Talepleri &amp; Çözülen Şikayetler</h4>
                    <ul>
                      {proposal.solved_complaints.map((item, idx) => (
                        <li key={idx}>
                          <span className="check-badge" aria-hidden="true">✓</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="risks-box">
                    <h4>⚠ Riskler &amp; Geliştirme Önerileri</h4>
                    <ul>
                      {proposal.risks.map((item, idx) => (
                        <li key={idx}>
                          <span className="warn-badge" aria-hidden="true">!</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="strategy-box">
                  <h4>Prototip ve Doğrulama Deneyi</h4>
                  <p>{proposal.prototype_plan || 'Doğrulama planı belirtilmedi.'}</p>
                  {proposal.need_ids && <p>İlgili ihtiyaçlar: {proposal.need_ids.join(', ')}</p>}
                  {proposal.evidence_ids && <p>Destekleyen kaynaklar: {proposal.evidence_ids.join(', ')}</p>}
                  {proposal.counter_evidence_ids && proposal.counter_evidence_ids.length > 0 && <p>Karşı kaynaklar: {proposal.counter_evidence_ids.join(', ')}</p>}
                </div>
                {/* 7. AI Nihai Değerlendirmesi */}
                {proposal.ai_verdict && (
                  <div className="ai-verdict-banner">
                    <span className="verdict-icon" aria-hidden="true">💡</span>
                    <div>
                      <strong>AI Direktörünün Gerekçeli Nihai Değerlendirmesi:</strong>
                      <p>{proposal.ai_verdict}</p>
                    </div>
                  </div>
                )}

                {/* 8. Doğrudan Kanıt Oyuncu Yorumları */}
                <div className="evidence-section">
                  <div className="evidence-section__header">
                    <h4>💬 İlişkilendirilen Kaynak Metinleri ({proposal.evidence_quotes.length} Alıntı)</h4>
                  </div>

                  <div className="evidence-cards-grid">
                    {proposal.evidence_quotes.map((ev, idx) => (
                      <blockquote key={idx} className={`store-review-card store-review-card--${ev.source}`}>
                        <div className="store-review-card__topbar">
                          <span className={`store-pill store-pill--${ev.source}`}>
                            {ev.source === 'app_store' && ' '}
                            {ev.source === 'google_play' && '▶ '}
                            {ev.source === 'reddit' && '◉ '}
                            {ev.source_label}
                          </span>
                          {ev.rating !== null && (
                            <span className="store-rating" title={`${ev.rating} / 5 yıldız`}>
                              {renderStars(ev.rating)}
                            </span>
                          )}
                        </div>
                        <div className="store-review-card__subject">{ev.subject}</div>
                        <p className="store-review-card__quote">“{ev.original_text || ev.quote}”</p>
                        <p className="source-note">{ev.data_origin === 'synthetic_demo' ? 'Sentetik test kaydı' : ev.data_origin === 'live' ? 'Canlı kaynaktan alınan özgün metin' : 'Eski kayıt: veri kökeni doğrulanmadı'}{ev.signal_kind ? ` · ${ev.signal_kind}` : ''}</p>
                        {ev.evidence_id && <p className="source-note">Kaynak kimliği: {ev.evidence_id}</p>}
                        {ev.fetched_at && <p className="source-note">Alınma zamanı: {formatScanTime(ev.fetched_at)}</p>}
                        {ev.translation_text && ev.translation_text !== (ev.original_text || ev.quote) && <p>Çeviri (özgün alıntı değildir): {ev.translation_text}</p>}
                        {ev.url && (
                          <div className="store-review-card__footer">
                            <a href={ev.url} target="_blank" rel="noreferrer">Kaynağı Gör ↗</a>
                          </div>
                        )}
                      </blockquote>
                    ))}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    )}
  </section>;
}
