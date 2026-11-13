import { useEffect, useState } from 'react';
import { getLatestScoutReport, runMarketScout } from '../../api/scout';
import type { AIProviderChoice, MarketScoutReport, ScoutMeta } from '../../domain/scout';
import { StatusMessage } from '../../components/StatusMessage';

export function OpportunityScoutPanel() {
  const [provider, setProvider] = useState<AIProviderChoice>('auto');
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
          setError(failure instanceof Error ? failure.message : 'Önceki piyasa taraması yüklenemedi.');
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
      const freshReport = await runMarketScout(provider);
      setReport(freshReport);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'AI piyasa taraması tamamlanamadı.');
    } finally {
      setScanning(false);
    }
  }

  return <section className="scout-section" aria-labelledby="scout-hero-title">
    <div className="scout-hero">
      <div className="scout-hero__content">
        <span className="eyebrow">OTONOM AI OYUN FIRSAT ARAŞTIRMACISI</span>
        <h2 id="scout-hero-title">Otonom AI Piyasa &amp; Oyun Fırsat Araştırmacısı</h2>
        <p>
          Tür seçmene gerek yok. AI; App Store, Google Play ve Reddit (<code>r/AndroidGaming</code>, <code>r/iosgaming</code>, <code>r/gamedev</code>)
          oyuncu yorumlarını tarar, insanların ne istediğini bulur ve yapılabilir oyun fikirlerini kanıtlarıyla çıkarır.
        </p>
        {meta && (
          <p className="scout-meta-note">
            Varsayılan AI motoru: <strong>{meta.configured_provider.toUpperCase()}</strong> · Yerel Ollama: <code>{meta.ollama_model}</code> ({meta.ollama_base_url})
            {meta.api_configured ? ' · Harici API anahtarı tanımlı' : ' · Harici API anahtarı opsiyonel (.env ile eklenebilir)'}
          </p>
        )}
      </div>
      <div className="scout-hero__actions">
        <label className="scout-provider-select">
          <span>AI Analiz Motoru</span>
          <select
            value={provider}
            onChange={event => setProvider(event.target.value as AIProviderChoice)}
            disabled={scanning}
          >
            <option value="auto">Otomatik (Yerel Ollama Öncelikli)</option>
            <option value="ollama">Yerel Ollama (Local LLM)</option>
            <option value="openai">Harici API (OpenAI)</option>
            <option value="gemini">Harici API (Gemini)</option>
          </select>
        </label>
        <button type="button" className="scout-cta-button" onClick={handleScan} disabled={scanning}>
          {scanning ? 'App Store, Play Store ve Reddit taranıyor, AI analiz ediyor…' : 'Piyasayı Tara ve Oyun Fırsatlarını Bul'}
        </button>
      </div>
    </div>

    {error && <StatusMessage kind="error" message={error} />}

    {loadingLatest && !report && (
      <p className="empty-state" role="status">Piyasa araştırma geçmişi kontrol ediliyor…</p>
    )}

    {!loadingLatest && !report && !scanning && (
      <div className="empty-state scout-empty">
        <h3>Henüz bir piyasa taraması çalıştırılmadı</h3>
        <p>
          Yukarıdaki <strong>“Piyasayı Tara ve Oyun Fırsatlarını Bul”</strong> butonuna tıkladığınızda AI;
          App Store, Google Play ve Reddit oyuncu topluluklarını tarayarak oyuncuların hangi türde nasıl bir oyun beklediğini raporlar.
        </p>
      </div>
    )}

    {report && (
      <div className="scout-results">
        <div className="scout-summary-bar" role="status">
          <div>
            <span className="eyebrow">AKTİF ANALİZ MOTORU</span>
            <strong>{report.ai_engine_label}</strong>
          </div>
          <div className="scout-badges">
            <span className="signal-pill signal-pill--appstore">App Store: {report.sources_summary.app_store_count} sinyal</span>
            <span className="signal-pill signal-pill--playstore">Google Play: {report.sources_summary.google_play_count} sinyal</span>
            <span className="signal-pill signal-pill--reddit">Reddit Toplulukları: {report.sources_summary.reddit_count} sinyal</span>
            <span className="signal-pill signal-pill--total">Toplam: {report.sources_summary.total_signals} kanıt</span>
          </div>
        </div>

        {report.warnings.length > 0 && (
          <div className="scout-warnings">
            {report.warnings.map((warning, idx) => (
              <p key={idx} className="source-note">ℹ️ {warning}</p>
            ))}
          </div>
        )}

        <div className="scout-block">
          <div className="section-toolbar">
            <div>
              <span className="eyebrow">AI KARARI · İNSANLAR BU TÜRDEN BÖYLE OYUN İSTİYOR</span>
              <h3>Şu Oyun Yapılabilir! ({report.actionable_game_proposals.length} Somut Fırsat)</h3>
            </div>
          </div>

          <div className="proposal-grid">
            {report.actionable_game_proposals.map(proposal => (
              <article key={proposal.opportunity_id} className="proposal-card">
                <div className="proposal-card__header">
                  <span className="proposal-genre-badge">Önerilen Tür: {proposal.recommended_genre}</span>
                  <span className="proposal-verdict-badge">ŞU OYUN YAPILABİLİR</span>
                </div>
                <h4>{proposal.concept_title}</h4>
                <p className="proposal-tagline">{proposal.tagline}</p>

                <div className="proposal-highlight">
                  <strong>İnsanlar Neden Bunu İstiyor?</strong>
                  <p>{proposal.why_people_want_this}</p>
                </div>

                <div className="proposal-details-grid">
                  <div>
                    <h5>Temel Oynanış Döngüsü (Core Loop)</h5>
                    <p>{proposal.core_loop}</p>
                  </div>
                  <div>
                    <h5>Hedef Kitle</h5>
                    <p>{proposal.target_audience}</p>
                  </div>
                  <div>
                    <h5>Adil Gelir Modeli</h5>
                    <p>{proposal.monetization_model}</p>
                  </div>
                  <div>
                    <h5>İlk 2 Haftalık Prototip Planı</h5>
                    <p>{proposal.prototype_plan}</p>
                  </div>
                </div>

                <div className="proposal-lists">
                  <div>
                    <h5>Çözülen Oyuncu Şikayetleri</h5>
                    <ul>
                      {proposal.solved_complaints.map((item, idx) => <li key={idx}>✓ {item}</li>)}
                    </ul>
                  </div>
                  <div>
                    <h5>Riskler &amp; Dikkat Edilecekler</h5>
                    <ul>
                      {proposal.risks.map((item, idx) => <li key={idx}>⚠ {item}</li>)}
                    </ul>
                  </div>
                </div>

                <div className="proposal-evidence">
                  <h5>Doğrudan Kanıt Yorumlar (App Store, Google Play &amp; Reddit)</h5>
                  <div className="evidence-list">
                    {proposal.evidence_quotes.map((ev, idx) => (
                      <blockquote key={idx} className="evidence-quote">
                        <div className="evidence-quote__top">
                          <span className={`source-badge source-badge--${ev.source}`}>{ev.source_label}</span>
                          <strong>{ev.subject}</strong>
                          {ev.rating !== null && <span className="rating-badge">★ {ev.rating}/5</span>}
                        </div>
                        <p>“{ev.quote}”</p>
                      </blockquote>
                    ))}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>

        <div className="scout-block">
          <div className="section-toolbar">
            <div>
              <span className="eyebrow">PAZAR TALEBİ ANALİZİ</span>
              <h3>Piyasada Yükselen Tür Talepleri ve Oyuncu Açlığı</h3>
            </div>
          </div>
          <div className="insight-grid">
            {report.top_genre_insights.map((insight, idx) => (
              <article key={idx} className="insight-card">
                <div className="insight-card__top">
                  <h4>{insight.genre}</h4>
                  <span className="demand-badge">{insight.demand_badge}</span>
                </div>
                <p>{insight.summary}</p>
                <div className="insight-columns">
                  <div>
                    <h5>Mevcut Oyunlardaki Şikayetler</h5>
                    <ul>
                      {insight.pain_points.map((point, pIdx) => <li key={pIdx}>{point}</li>)}
                    </ul>
                  </div>
                  <div>
                    <h5>Oyuncuların İstediği Mekanikler</h5>
                    <ul>
                      {insight.requested_mechanics.map((mech, mIdx) => <li key={mIdx}>{mech}</li>)}
                    </ul>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    )}
  </section>;
}
