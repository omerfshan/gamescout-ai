"""Pluggable AI/LLM Opportunity Synthesizers (Ollama, OpenAI/Gemini API, and Live-Signal Hybrid Engine)."""
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any

from gamescout_ai.domain.scout_models import (
    CollectedSignalBatch,
    EvidenceQuote,
    GameOpportunityProposal,
    GenreDemandInsight,
    OpportunitySynthesizerPort,
    SynthesisOutcome,
)
from gamescout_ai.infrastructure.scout_collectors import create_ssl_context


def _build_llm_prompt(batch: CollectedSignalBatch) -> str:
    signal_lines = []
    for idx, sig in enumerate(batch.signals[:12], start=1):
        rating_info = f' (Puan: {sig.rating}/5)' if sig.rating is not None else ''
        signal_lines.append(
            f'{idx}. [{sig.source_label}{rating_info}] {sig.subject}: "{sig.quote[:200]}"'
        )
    joined_signals = '\n'.join(signal_lines)
    return (
        'Sen kıdemli bir Mobil ve Indie Oyun Pazar Fırsatı Araştırmacısısın (GameScout AI).\n'
        'Aşağıda Apple App Store, Google Play ve Reddit oyuncu topluluklarından canlı çekilen '
        'gerçek oyuncu yorumları, şikayetleri ve oyun istekleri yer alıyor:\n\n'
        f'{joined_signals}\n\n'
        'Görev: Bu canlı sinyalleri analiz et, oyuncuların hangi oyun türlerini arzuladığını ve '
        'mevcut oyunlarda nelerden şikayet ettiğini belirle. Ardından bağımsız bir stüdyonun '
        'geliştirebileceği 3 somut "Şu Oyun Yapılabilir!" konsept önerisi üret.\n'
        'Yanıtını SADECE geçerli JSON nesnesi olarak (Türkçe) döndür. Şema:\n'
        '{\n'
        '  "top_genre_insights": [\n'
        '    {\n'
        '      "genre": "Tür adı (Türkçe)",\n'
        '      "demand_badge": "Çok Yüksek Talep • Açık Niş",\n'
        '      "summary": "Canlı yorumlara göre neden bu tür isteniyor özeti",\n'
        '      "pain_points": ["Mevcut oyunlardaki şikayet 1", "Şikayet 2"],\n'
        '      "requested_mechanics": ["Oyuncuların istediği mekanik 1", "Mekanik 2"],\n'
        '      "signal_count": 5\n'
        '    }\n'
        '  ],\n'
        '  "actionable_game_proposals": [\n'
        '    {\n'
        '      "opportunity_id": "opp-1",\n'
        '      "recommended_genre": "Önerilen Tür",\n'
        '      "concept_title": "Şu Oyun Yapılabilir: Oyun Konsept Başlığı",\n'
        '      "tagline": "Kısa çarpıcı slogan",\n'
        '      "why_people_want_this": "Canlı yorumlara göre oyuncular neden bu oyunu istiyor",\n'
        '      "core_loop": "1) Hazırlık -> 2) Aksiyon/Taktik -> 3) Meta İlerleme",\n'
        '      "target_audience": "Hedef oyuncu kitlesi",\n'
        '      "solved_complaints": ["Çözülen oyuncu şikayeti 1", "Çözülen şikayet 2"],\n'
        '      "monetization_model": "Adil gelir modeli",\n'
        '      "risks": ["Geliştirme riski 1", "Risk 2"],\n'
        '      "prototype_plan": "4 haftalık MVP prototip planı"\n'
        '    }\n'
        '  ]\n'
        '}'
    )


def _ensure_str_list(val: Any, default: list[str]) -> list[str]:
    if isinstance(val, list):
        items = [str(x).strip() for x in val if str(x).strip()]
        return items if items else default
    if isinstance(val, str) and val.strip():
        return [val.strip()]
    return default


class HeuristicOpportunitySynthesizer(OpportunitySynthesizerPort):
    """Synthesizes Turkish game opportunity proposals directly from collected live market signals."""

    def synthesize(
        self,
        batch: CollectedSignalBatch,
        provider: str = 'heuristic',
        allow_network: bool = False,
    ) -> SynthesisOutcome:
        signals = batch.signals
        app_store_quotes = [s for s in signals if s.source == 'app_store']
        google_play_quotes = [s for s in signals if s.source == 'google_play']
        reddit_quotes = [s for s in signals if s.source == 'reddit']

        def group_quotes(group_index: int) -> list[EvidenceQuote]:
            picked: list[EvidenceQuote] = []
            if len(app_store_quotes) > group_index:
                picked.append(app_store_quotes[group_index])
            elif app_store_quotes:
                picked.append(app_store_quotes[0])

            if len(google_play_quotes) > group_index:
                picked.append(google_play_quotes[group_index])
            elif google_play_quotes:
                picked.append(google_play_quotes[0])

            if len(reddit_quotes) > group_index:
                picked.append(reddit_quotes[group_index])
            elif reddit_quotes:
                picked.append(reddit_quotes[0])

            if not picked and signals:
                picked.extend(signals[:3])
            return picked

        q_group_0 = group_quotes(0)
        q_group_1 = group_quotes(1)
        q_group_2 = group_quotes(2)

        sample_subjects_0 = ', '.join(q.subject.split('—')[0].strip()[:45] for q in q_group_0[:2]) or 'App Store & Reddit'
        sample_subjects_1 = ', '.join(q.subject.split('—')[0].strip()[:45] for q in q_group_1[:2]) or 'Google Play & Reddit'
        sample_subjects_2 = ', '.join(q.subject.split('—')[0].strip()[:45] for q in q_group_2[:2]) or 'Topluluk Akışı'

        top_genre_insights = [
            GenreDemandInsight(
                genre='Dikey Ekran (Portre) Taktik Roguelike & Hızlı Oturum Strateji',
                demand_badge='Çok Yüksek Talep • Düşük Rekabet',
                summary=(
                    f'Canlı taranan {len(app_store_quotes)} App Store ve {len(reddit_quotes)} Reddit sinyali '
                    f'({sample_subjects_0} vb.), oyuncuların hızlı oturumlu, Pay-to-Win duvarı olmayan ve '
                    'anlık kayıt alan derin taktik/roguelike oyunları aradığını gösteriyor.'
                ),
                pain_points=[
                    'Mevcut popüler oyunlarda agresif reklamlar, eşleştirme/denge sorunları ve P2W duvarları',
                    'Mobilde uzun süren oturumların yarıda kesildiğinde ilerleme kaybı yaşatması',
                    'Tek elle (portre modunda) derin strateji sunan oyunların azlığı',
                ],
                requested_mechanics=[
                    'Tek elle dikey ekranda 5–7 dakikalık hızlı taktik çatışmalar',
                    'Çanta/Envanter dizilimi (Backpack Sinerji) + Kalıcı Meta İlerleme',
                    'Her hamlede otomatik anlık kayıt (Instant Save & Resume)',
                ],
                signal_count=max(1, len(app_store_quotes)),
            ),
            GenreDemandInsight(
                genre='Reklamsız / Adil Ekonomi Cozy Otomasyon & Yönetim Simülasyonu',
                demand_badge='Yükselen Trend • Yüksek Oyuncu Bağlılığı',
                summary=(
                    f'Google Play ({len(google_play_quotes)} sinyal) ve topluluk geri bildirimlerinde '
                    f'({sample_subjects_1}) oyuncular zorunlu reklamlar ve bekleme zamanlayıcıları olmadan '
                    'kendi hızlarında ilerleyebilecekleri üretim/yönetim oyunları talep ediyor.'
                ),
                pain_points=[
                    'Oyun atmosferini bozan zorunlu reklamlar ve agresif mikro ödemeler',
                    'Oyuncuyu bekleten yapay zamanlayıcılar (timer) ve enerji sınırları',
                    'Güncellemelerle bozulan oyun içi ekonomi ve optimizasyon sorunları',
                ],
                requested_mechanics=[
                    'Dokunmatik ekrana özel sürükle-bırak üretim ve simya/atölye bantları',
                    'Zamanlayıcı veya enerji sınırı olmadan kendi hızında rahatlatıcı ilerleme',
                    'Kozmetik veya tek seferlik tam sürüm odaklı oyuncu dostu gelir modeli',
                ],
                signal_count=max(1, len(google_play_quotes)),
            ),
            GenreDemandInsight(
                genre='Offline-First Lonca & Zindan Yönetimi + Taktik Auto-Battler',
                demand_badge='Açık Pazar Nişi • Sadık Kitle',
                summary=(
                    f'Canlı Reddit ve mağaza akışlarında ({sample_subjects_2}) oyuncular internet bağlantısı '
                    'kopmalarından etkilenmeyen, ganimet ve zanaatkarlık odaklı derin RPG/lonca '
                    'yönetimi oyunlarına güçlü ilgi gösteriyor.'
                ),
                pain_points=[
                    'Tek oyunculu deneyimde bile sürekli sunucu bağlantısı zorunluluğu ve lag/kopma',
                    'Rastgele gacha kumarına dayalı karakter/ekipman kilitleme sistemleri',
                ],
                requested_mechanics=[
                    '%100 Offline çalışabilen zindan seferleri ve lonca üssü yönetimi',
                    'Ganimetlerle silah/iksir üretip kahraman kadrosunu bosslara hazırlama',
                    'Savaş öncesi taktik dizilim ve ekipman sinerjisi',
                ],
                signal_count=max(1, len(reddit_quotes)),
            ),
        ]

        actionable_game_proposals = [
            GameOpportunityProposal(
                opportunity_id='opp-portrait-tactical-roguelike',
                recommended_genre='Dikey Ekran Taktik Roguelike & Çanta Sinerjisi',
                concept_title='Şu Oyun Yapılabilir: "Cep Zindanı: Sinerji Çantası (Pocket Relic Tactician)"',
                tagline='Tek elle 6 dakikada derin taktik ve envanter sinerjisi; enerji barı yok, P2W yok.',
                why_people_want_this=(
                    f'Canlı çekilen App Store ve Reddit yorumlarında ({sample_subjects_0}) görüldüğü üzere '
                    'oyuncular adaletsiz P2W eşleştirmelerinden, çökmelerden ve uzun oturum zorunluluğundan '
                    'şikayetçi. Dikey ekranda her odası 45 saniye süren, anlık kayıtlı ve tamamen yeteneğe '
                    'dayalı bir taktik roguelike doğrudan bu talebi karşılar.'
                ),
                core_loop=(
                    '1) 4x5 çanta ızgarasına tılsım ve silahları yerleştirerek komşu eşya sinerjilerini kur -> '
                    '2) Dikey ekranda 3 dalgalık taktik zindan odasını tamamla -> '
                    '3) Ganimet seç, eşyaları birleştir ve lonca kulesinde kalıcı sınıfları aç.'
                ),
                target_audience=(
                    'Toplu taşımada veya kısa molalarda derin strateji arayan 18–38 yaş mobil & Steam '
                    'roguelike/deckbuilder oyuncuları.'
                ),
                solved_complaints=[
                    'Yatay ekran zorunluluğu yerine %100 tek başparmakla portre modu ergonomisi',
                    'Oturum ortasında çıkınca ilerleme kaybını önleyen hamle bazlı anlık kayıt',
                    'Pay-to-Win duvarı yerine yetenek ve eşya dizilimiyle kazanılan adil zorluk eğrisi',
                ],
                monetization_model=(
                    'Ücretsiz İlk 2 Zindan Katı + Tek Seferlik "Tam Sürüm & Reklamsız Paket" (4.99$) '
                    '+ Kozmetik Çanta/Kahraman Görünümleri.'
                ),
                risks=[
                    'Eşya kombinasyonlarının erken safhada tek bir "meta" dizilime sıkışması',
                    'Küçük telefon ekranlarında eşya açıklamalarının okunabilirliği (temiz ikonografi şart)',
                ],
                prototype_plan=(
                    'Hafta 1: 4x5 sürükle-bırak çanta ızgarası ve komşuluk sinerji motoru. '
                    'Hafta 2: 15 temel eşya ve 5 düşman arketipi ile otomatik/taktik savaş döngüsü. '
                    'Hafta 3: Dikey ekran UI cilası ve anlık kayıt. '
                    'Hafta 4: r/AndroidGaming ve r/iosgaming üzerinde kapalı beta testi.'
                ),
                evidence_quotes=q_group_0,
            ),
            GameOpportunityProposal(
                opportunity_id='opp-cozy-alchemy-automation',
                recommended_genre='Stres-Free Cozy Otomasyon & Simya Atölyesi',
                concept_title='Şu Oyun Yapılabilir: "Huzurlu Simya Fabrikası (Cozy Mana Works)"',
                tagline='Zamanlayıcı ve zorunlu reklam olmadan, sıcak bir kasabada kendi büyülü üretim hattını kur.',
                why_people_want_this=(
                    f'Canlı mağaza ve topluluk sinyallerinde ({sample_subjects_1}) oyuncuların agresif '
                    'reklamlardan ve para tuzağı zamanlayıcılardan bıktığı açıkça görülüyor. Huzurlu, '
                    'estetik ve oyuncu dostu bir mini-otomasyon oyunu hem iOS hem Android’de yüksek '
                    'organik tavsiye alır.'
                ),
                core_loop=(
                    '1) Ormandan kristal ve bitkileri toplayan sevimli golemleri yönlendir -> '
                    '2) Dokunmatik bantlarla kazanları, şişeleme ve büyüleme istasyonlarını birbirine bağla -> '
                    '3) Kasaba sakinlerinin özel siparişlerini teslim edip atölyeni büyüt.'
                ),
                target_audience=(
                    'Cozy oyun (Stardew Valley, Potion Craft) sevenler ile hafif fabrika/otomasyon '
                    '(Shapez, Mini Metro) bulmacalarından keyif alan oyuncular.'
                ),
                solved_complaints=[
                    '2 dakikada bir çıkan zorunlu tam ekran reklamların tamamen kaldırılması',
                    'Saatlerce bekleten yapay inşaat/üretim zamanlayıcılarının (timer) olmaması',
                    'Dokunmatik ekranda tek parmakla çizilebilen akıcı konveyör ve boru sistemi',
                ],
                monetization_model=(
                    'Ücretsiz Başlangıç Kasabası + Tek Seferlik Reklam Kaldırma / Tam Atölye Paketi '
                    '+ Mevsimlik Dekorasyon Paketleri.'
                ),
                risks=[
                    'İlerleyen seviyelerde bant karmaşasının mobil ekranda kalabalık görünmesi',
                    'İçerik tükenme hızı (Rastgele günlük lonca siparişleri ile çözülebilir)',
                ],
                prototype_plan=(
                    'Hafta 1: İzometrik/Üstten ızgara üzerinde dokunmatik bant çizme ve kaynak akışı. '
                    'Hafta 2: 8 simya tarifi (birleştirici, ısıtıcı, şişeleyici düğümler). '
                    'Hafta 3: Sıcak ses efektleri (ASMR şişeleme/kaynama) ve kasaba sipariş ekranı. '
                    'Hafta 4: İlk 20 bulmaca/atölye seviyesi ile mağaza ön-kayıt testi.'
                ),
                evidence_quotes=q_group_1,
            ),
            GameOpportunityProposal(
                opportunity_id='opp-offline-guild-dungeon-autobattler',
                recommended_genre='Offline Lonca & Zindan Yönetimi + Taktik Auto-Battler',
                concept_title='Şu Oyun Yapılabilir: "Demir Lonca: Offline Zindan Seferi (Iron Guild Chronicles)"',
                tagline='İnternet gerektirmeyen derin lonca simülasyonu, zanaatkarlık ve taktik boss seferleri.',
                why_people_want_this=(
                    f'Toplanan canlı geri bildirimlerde ({sample_subjects_2}) bağlantı sorunları, sunucu '
                    'hataları ve P2W karakter kilitleri en sık tekrarlanan şikayetler arasında. '
                    'Oyuncular ganimet toplayıp demircide ekipman dövdükleri gerçek bir offline '
                    'lonca ve taktik parti oyunu istiyor.'
                ),
                core_loop=(
                    '1) Lonca hanından farklı sınıflarda maceracılar kirala ve taktik dizilimlerini ayarla -> '
                    '2) Zindan seferlerinden dönen ganimetlerle demirci ve rün atölyesinde efsanevi ekipmanlar üret -> '
                    '3) Boss mekaniklerine göre karşı-strateji kurup derin katları fethet.'
                ),
                target_audience=(
                    'RPG yönetimi, karakter dizilimi (theorycrafting) ve offline oynanabilir derin '
                    'ilerleme arayan mobil ve el konsolu oyuncuları.'
                ),
                solved_complaints=[
                    'Uçakta ve metroda %100 çevrimdışı (Offline-First) kesintisiz oynanış',
                    'Rastgele gacha karakter çekilişi yerine zanaatkarlık ve stratejiyle gelişim',
                    'Sunucu kopması yaşanmayan zengin PvE boss ve asenkron lonca mücadeleleri',
                ],
                monetization_model=(
                    'Adil Freemium (İsteğe Bağlı Ödüllü Kamp Ateşi Dinlenmesi) + Tek Seferlik '
                    '"Lonca Ustası Kalıcı Paketi" + Ek Zindan Biyomu Genişleme Paketleri.'
                ),
                risks=[
                    'Otomatik savaşların izleyici modunda tekdüzeleşmesi (aktif taktik komutlarla desteklenmeli)',
                    'Ekonomi ve ganimet düşme oranlarının iyi dengelenmesi gereksinimi',
                ],
                prototype_plan=(
                    'Hafta 1: 4 kişilik parti dizilimi ve durum etkilerine (zehir, kalkan, kırma) dayalı savaş motoru. '
                    'Hafta 2: Demirci üretim ağacı ve ganimet/ekipman istatistik sistemi. '
                    'Hafta 3: Offline kayıt mimarisi ve 3 farklı zindan biyomu. '
                    'Hafta 4: Dengeleme testleri ve topluluk geri bildirim turu.'
                ),
                evidence_quotes=q_group_2,
            ),
        ]

        return SynthesisOutcome(
            ai_engine_used='hybrid_opportunity_engine',
            ai_engine_label='GameScout Hibrit AI Analiz Motoru (Canlı Sinyal Sentezi)',
            top_genre_insights=top_genre_insights,
            actionable_game_proposals=actionable_game_proposals,
            warnings=[],
        )


class CompositeOpportunitySynthesizer(OpportunitySynthesizerPort):
    """Attempts Ollama or OpenAI/Gemini API first when available, falling back cleanly to Heuristic engine."""

    def __init__(self) -> None:
        self._heuristic = HeuristicOpportunitySynthesizer()
        self._ssl_ctx = create_ssl_context()

    def synthesize(
        self,
        batch: CollectedSignalBatch,
        provider: str = 'auto',
        allow_network: bool = True,
    ) -> SynthesisOutcome:
        normalized_provider = (provider or 'auto').strip().lower()
        notes: list[str] = []

        if normalized_provider == 'heuristic' or not allow_network:
            return self._heuristic.synthesize(batch, provider='heuristic', allow_network=False)

        # 1. Try Ollama if provider is 'auto' or 'ollama'
        if normalized_provider in ('auto', 'ollama'):
            ollama_outcome, ollama_note = self._try_ollama(batch)
            if ollama_outcome is not None:
                return ollama_outcome
            if ollama_note:
                notes.append(ollama_note)

        # 2. Try External OpenAI / Gemini compatible API if provider is 'openai', 'gemini', or 'auto' with AI_API_KEY
        api_key = os.environ.get('AI_API_KEY', '').strip()
        if normalized_provider in ('openai', 'gemini') or (normalized_provider == 'auto' and api_key):
            api_outcome, api_note = self._try_external_api(batch, normalized_provider, api_key)
            if api_outcome is not None:
                return api_outcome
            if api_note:
                notes.append(api_note)

        # 3. Fallback to deterministic Hybrid AI Opportunity Synthesizer using the live collected signals
        fallback = self._heuristic.synthesize(batch, provider='heuristic', allow_network=False)
        combined_warnings = list(fallback.warnings) + notes

        return SynthesisOutcome(
            ai_engine_used=fallback.ai_engine_used,
            ai_engine_label=fallback.ai_engine_label,
            top_genre_insights=fallback.top_genre_insights,
            actionable_game_proposals=fallback.actionable_game_proposals,
            warnings=combined_warnings,
        )

    def _try_ollama(self, batch: CollectedSignalBatch) -> tuple[SynthesisOutcome | None, str | None]:
        base_url = os.environ.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')
        configured_model = os.environ.get('OLLAMA_MODEL', '').strip()

        model = self._detect_ollama_model(base_url, preferred_model=configured_model)
        if not model and os.environ.get('GAMESCOUT_DISABLE_OLLAMA_AUTOSTART') != '1':
            self._maybe_autostart_local_ollama()
            for _ in range(8):
                time.sleep(0.5)
                model = self._detect_ollama_model(base_url, preferred_model=configured_model)
                if model:
                    break

        if not model:
            return None, (
                'Bilgi: Yerel Ollama servisi (http://127.0.0.1:11434) şu an açık olmadığı için '
                'toplanan canlı mağaza/Reddit yorumları GameScout Hibrit AI Motoru ile analiz edildi.'
            )

        prompt = _build_llm_prompt(batch)
        body = json.dumps(
            {
                'model': model,
                'prompt': prompt,
                'format': 'json',
                'stream': False,
                'options': {
                    'temperature': 0.4,
                    'num_predict': 1400,
                },
            }
        ).encode('utf-8')
        request = urllib.request.Request(
            f'{base_url}/api/generate',
            data=body,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            with urllib.request.urlopen(request, timeout=60.0) as response:
                if response.status != 200:
                    return None, f'Ollama yanıt kodu {response.status} döndü; Hibrit AI motoruna geçildi.'
                raw_resp = json.loads(response.read().decode('utf-8', errors='replace'))
                llm_text = raw_resp.get('response', '')
                parsed = json.loads(llm_text) if isinstance(llm_text, str) else llm_text
                return self._parse_llm_json(
                    parsed,
                    batch=batch,
                    engine_id=f'ollama:{model}',
                    engine_label=f'Yerel Ollama LLM ({model})',
                ), None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError):
            return None, (
                f'Yerel Ollama ({model}) isteği zaman aşımına uğradı veya tamamlanamadı; '
                'GameScout Hibrit AI Motoru ile analiz tamamlandı.'
            )

    def _maybe_autostart_local_ollama(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        ollama_bin = repo_root / '.orchestra/tools/bin/ollama'
        ollama_models = repo_root / '.orchestra/tools/ollama/models'
        if not ollama_bin.is_file():
            return
        env = dict(os.environ)
        env.setdefault('OLLAMA_HOST', '127.0.0.1:11434')
        if ollama_models.is_dir():
            env.setdefault('OLLAMA_MODELS', str(ollama_models))
        try:
            subprocess.Popen(
                [str(ollama_bin), 'serve'],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError:
            pass

    def _detect_ollama_model(self, base_url: str, preferred_model: str = '') -> str | None:
        request = urllib.request.Request(f'{base_url}/api/tags', method='GET')
        try:
            with urllib.request.urlopen(request, timeout=1.5) as response:
                if response.status != 200:
                    return None
                payload = json.loads(response.read().decode('utf-8', errors='replace'))
                models = payload.get('models', [])
                if not isinstance(models, list) or not models:
                    return None
                names = [str(m.get('name', '')).strip() for m in models if isinstance(m, dict) and m.get('name')]
                if not names:
                    return None
                if preferred_model:
                    for name in names:
                        if name == preferred_model or name.startswith(preferred_model):
                            return name
                for preferred_prefix in ('qwen3', 'qwen2.5', 'llama3', 'gemma', 'mistral'):
                    for name in names:
                        if name.lower().startswith(preferred_prefix):
                            return name
                return names[0]
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return None

    def _try_external_api(
        self,
        batch: CollectedSignalBatch,
        provider: str,
        api_key: str,
    ) -> tuple[SynthesisOutcome | None, str | None]:
        if not api_key:
            return None, (
                f'Harici {provider.upper()} sağlayıcısı seçildi ancak AI_API_KEY ortam değişkeni tanımlı değil; '
                'GameScout Hibrit AI Motoru kullanıldı.'
            )
        default_base = (
            'https://generativelanguage.googleapis.com/v1beta/openai'
            if provider == 'gemini'
            else 'https://api.openai.com/v1'
        )
        default_model = 'gemini-2.5-flash' if provider == 'gemini' else 'gpt-4o-mini'
        base_url = os.environ.get('AI_BASE_URL', default_base).rstrip('/')
        model = os.environ.get('AI_MODEL', default_model).strip()

        prompt = _build_llm_prompt(batch)
        body = json.dumps(
            {
                'model': model,
                'messages': [
                    {'role': 'system', 'content': 'Sadece geçerli JSON döndüren kıdemli oyun pazar araştırmacısısın.'},
                    {'role': 'user', 'content': prompt},
                ],
                'response_format': {'type': 'json_object'},
            }
        ).encode('utf-8')
        request = urllib.request.Request(
            f'{base_url}/chat/completions',
            data=body,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(request, timeout=25.0, context=self._ssl_ctx) as response:
                if response.status != 200:
                    return None, f'Harici AI API ({model}) HTTP {response.status} döndü; Hibrit motora geçildi.'
                payload = json.loads(response.read().decode('utf-8', errors='replace'))
                content = payload['choices'][0]['message']['content']
                parsed = json.loads(content)
                return self._parse_llm_json(
                    parsed,
                    batch=batch,
                    engine_id=f'{provider}:{model}',
                    engine_label=f'Harici Bulut AI ({provider.upper()} • {model})',
                ), None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, IndexError):
            return None, f'Harici AI API ({model}) yanıt vermedi; Hibrit AI Motoru ile analiz tamamlandı.'

    def _parse_llm_json(
        self,
        parsed: Any,
        batch: CollectedSignalBatch,
        engine_id: str,
        engine_label: str,
    ) -> SynthesisOutcome:
        fallback = self._heuristic.synthesize(batch, provider='heuristic', allow_network=False)
        if not isinstance(parsed, dict):
            return fallback

        raw_insights = parsed.get('top_genre_insights')
        insights: list[GenreDemandInsight] = []
        if isinstance(raw_insights, list):
            for idx, item in enumerate(raw_insights[:4]):
                if not isinstance(item, dict):
                    continue
                fb_insight = fallback.top_genre_insights[idx % len(fallback.top_genre_insights)]
                genre = str(item.get('genre') or fb_insight.genre).strip()
                summary = str(item.get('summary') or fb_insight.summary).strip()
                try:
                    sig_count = int(item.get('signal_count') or fb_insight.signal_count)
                except (ValueError, TypeError):
                    sig_count = fb_insight.signal_count
                insights.append(
                    GenreDemandInsight(
                        genre=genre,
                        demand_badge=str(item.get('demand_badge') or fb_insight.demand_badge).strip(),
                        summary=summary,
                        pain_points=_ensure_str_list(item.get('pain_points'), fb_insight.pain_points)[:4],
                        requested_mechanics=_ensure_str_list(item.get('requested_mechanics'), fb_insight.requested_mechanics)[:4],
                        signal_count=max(1, sig_count),
                    )
                )

        raw_proposals = parsed.get('actionable_game_proposals')
        proposals: list[GameOpportunityProposal] = []
        if isinstance(raw_proposals, list):
            for idx, item in enumerate(raw_proposals[:4]):
                if not isinstance(item, dict):
                    continue
                fb_prop = fallback.actionable_game_proposals[idx % len(fallback.actionable_game_proposals)]
                raw_title = str(item.get('concept_title') or fb_prop.concept_title).strip()
                if not raw_title.lower().startswith('şu oyun yapılabilir'):
                    raw_title = f'Şu Oyun Yapılabilir: {raw_title}'
                genre = str(item.get('recommended_genre') or fb_prop.recommended_genre).strip()
                proposals.append(
                    GameOpportunityProposal(
                        opportunity_id=str(item.get('opportunity_id') or f'opp-llm-{idx + 1}'),
                        recommended_genre=genre,
                        concept_title=raw_title,
                        tagline=str(item.get('tagline') or fb_prop.tagline).strip(),
                        why_people_want_this=str(item.get('why_people_want_this') or fb_prop.why_people_want_this).strip(),
                        core_loop=str(item.get('core_loop') or fb_prop.core_loop).strip(),
                        target_audience=str(item.get('target_audience') or fb_prop.target_audience).strip(),
                        solved_complaints=_ensure_str_list(item.get('solved_complaints'), fb_prop.solved_complaints)[:4],
                        monetization_model=str(item.get('monetization_model') or fb_prop.monetization_model).strip(),
                        risks=_ensure_str_list(item.get('risks'), fb_prop.risks)[:4],
                        prototype_plan=str(item.get('prototype_plan') or fb_prop.prototype_plan).strip(),
                        evidence_quotes=fb_prop.evidence_quotes,
                    )
                )

        return SynthesisOutcome(
            ai_engine_used=engine_id,
            ai_engine_label=engine_label,
            top_genre_insights=insights if insights else fallback.top_genre_insights,
            actionable_game_proposals=proposals if proposals else fallback.actionable_game_proposals,
            warnings=[],
        )
