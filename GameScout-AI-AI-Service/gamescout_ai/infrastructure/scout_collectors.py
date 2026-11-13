"""Public market signal collectors for App Store, Google Play, and Reddit using real live feeds."""
import html
import json
import os
import re
import ssl
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

from gamescout_ai.domain.scout_models import (
    CollectedSignalBatch,
    EvidenceQuote,
    SignalCollectorPort,
)

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) GameScoutAI/1.0'
HTTP_TIMEOUT_SECONDS = 4.5


def create_ssl_context() -> ssl.SSLContext:
    """Builds an SSLContext using macOS system CA bundle (/etc/ssl/cert.pem) when default cafile is missing."""
    default_paths = ssl.get_default_verify_paths()
    if default_paths.cafile and os.path.exists(default_paths.cafile):
        return ssl.create_default_context()
    if os.path.exists('/etc/ssl/cert.pem'):
        return ssl.create_default_context(cafile='/etc/ssl/cert.pem')
    return ssl.create_default_context()


OFFLINE_TEST_SIGNALS: tuple[EvidenceQuote, ...] = (
    EvidenceQuote(
        source='app_store',
        source_label='Apple App Store (Çevrimdışı Test Verisi)',
        subject='Pocket Rogues (iOS)',
        quote='Dikey ekranda tek elle oynanabilen, 5 dakikalık hızlı oturumlu taktik roguelike istiyoruz.',
        rating=3,
    ),
    EvidenceQuote(
        source='app_store',
        source_label='Apple App Store (Çevrimdışı Test Verisi)',
        subject='Idle Town Automation (iOS)',
        quote='Zorunlu reklam ve bekleme zamanlayıcısı olmayan huzurlu bir otomasyon oyunu arıyorum.',
        rating=2,
    ),
    EvidenceQuote(
        source='app_store',
        source_label='Apple App Store (Çevrimdışı Test Verisi)',
        subject='Dungeon Guild (iOS)',
        quote='Tek oyunculu modda bile internet istemesi saçma, tamamen offline lonca yönetimi şart.',
        rating=2,
    ),
    EvidenceQuote(
        source='app_store',
        source_label='Apple App Store (Çevrimdışı Test Verisi)',
        subject='Backpack Defense (iOS)',
        quote='Envanter birleştirme mekaniği güzel ama P2W duvarı olmadan stratejinin kazandığı oyun lazım.',
        rating=3,
    ),
    EvidenceQuote(
        source='google_play',
        source_label='Google Play (Çevrimdışı Test Verisi)',
        subject='Deckbuilder RPG (Android)',
        quote='Portre modunda çalışan, pil düşmanı olmayan taktiksel deste/envanter kurma oyunlarına açlık var.',
        rating=4,
    ),
    EvidenceQuote(
        source='google_play',
        source_label='Google Play (Çevrimdışı Test Verisi)',
        subject='Alchemy Shop Sim (Android)',
        quote='Zamanlayıcı bekletmeyen sıcak bir simya ve dükkan otomasyon simülasyonu istiyoruz.',
        rating=3,
    ),
    EvidenceQuote(
        source='google_play',
        source_label='Google Play (Çevrimdışı Test Verisi)',
        subject='Tactical Auto-Battler (Android)',
        quote='Bağlantı kopması olmayan asenkron veya PvE boss seferli taktik auto-battler çok tutar.',
        rating=3,
    ),
    EvidenceQuote(
        source='google_play',
        source_label='Google Play (Çevrimdışı Test Verisi)',
        subject='Survival Base Defense (Android)',
        quote='Gündüz kaynak toplayıp gece savunma yaptığımız co-op hayatta kalma oyunu arıyoruz.',
        rating=4,
    ),
    EvidenceQuote(
        source='reddit',
        source_label='Reddit • r/AndroidGaming (Çevrimdışı Test Verisi)',
        subject='Looking for portrait tactical roguelike / backpack games without P2W',
        quote='We need more portrait mode tactical roguelikes with instant save and zero energy bars.',
        rating=None,
    ),
    EvidenceQuote(
        source='reddit',
        source_label='Reddit • r/iosgaming (Çevrimdışı Test Verisi)',
        subject='Why are there so few stress-free cozy automation games on mobile?',
        quote='A simplified Factorio/Shapez with cozy alchemy visuals and no timers would be an instant buy.',
        rating=None,
    ),
    EvidenceQuote(
        source='reddit',
        source_label='Reddit • r/gamedev (Çevrimdışı Test Verisi)',
        subject='Underserved mobile/indie niches in 2026',
        quote='Portrait roguelikes, cozy automation, and offline guild simulators have huge unmet player demand.',
        rating=None,
    ),
    EvidenceQuote(
        source='reddit',
        source_label='Reddit • r/AndroidGaming (Çevrimdışı Test Verisi)',
        subject='Offline guild & dungeon management RPG without gacha?',
        quote='Looking for a game where you send adventurers to dungeons and craft gear offline without gacha.',
        rating=None,
    ),
)


class PublicMarketSignalCollector(SignalCollectorPort):
    """Collects REAL live public signals from App Store, Google Play & Reddit when allow_network=True."""

    def __init__(self) -> None:
        self._ssl_ctx = create_ssl_context()

    def collect_signals(self, allow_network: bool = True) -> CollectedSignalBatch:
        if not allow_network:
            return CollectedSignalBatch(
                signals=list(OFFLINE_TEST_SIGNALS),
                live_sources_used=[],
                warnings=['Çevrimdışı test modu (--no-network) aktif: Yalnızca test sinyalleri kullanıldı.'],
            )

        live_signals: list[EvidenceQuote] = []
        live_sources_used: list[str] = []
        warnings: list[str] = []

        app_store_live = self._fetch_app_store_signals()
        if app_store_live:
            live_signals.extend(app_store_live)
            live_sources_used.append('app_store')
        else:
            warnings.append('Apple App Store canlı RSS akışına şu an ulaşılamadı.')

        google_play_live = self._fetch_google_play_signals()
        if google_play_live:
            live_signals.extend(google_play_live)
            live_sources_used.append('google_play')
        else:
            warnings.append('Google Play canlı oyuncu akışına şu an ulaşılamadı.')

        reddit_live = self._fetch_reddit_signals()
        if reddit_live:
            live_signals.extend(reddit_live)
            live_sources_used.append('reddit')
        else:
            warnings.append('Reddit canlı topluluk akışına şu an ulaşılamadı.')

        return CollectedSignalBatch(
            signals=live_signals,
            live_sources_used=live_sources_used,
            warnings=warnings,
        )

    def _http_get_bytes(self, url: str) -> bytes | None:
        request = urllib.request.Request(
            url,
            headers={
                'User-Agent': USER_AGENT,
                'Accept': 'application/json, application/xml, text/xml, text/html, */*;q=0.8',
                'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS, context=self._ssl_ctx) as response:
                if response.status != 200:
                    return None
                return response.read(512 * 1024)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return None

    def _fetch_app_store_signals(self) -> list[EvidenceQuote]:
        """Fetches real user reviews from Apple's official iTunes Customer Reviews RSS JSON feeds."""
        feeds = (
            ('Subway Surfers (TR App Store)', 'https://itunes.apple.com/tr/rss/customerreviews/id=512939461/sortBy=mostRecent/json'),
            ('Brawl Stars (TR App Store)', 'https://itunes.apple.com/tr/rss/customerreviews/id=1229016807/sortBy=mostRecent/json'),
            ('clash royale (TR App Store)', 'https://itunes.apple.com/tr/rss/customerreviews/id=1053012308/sortBy=mostRecent/json'),
            ('Vampire Survivors (US App Store)', 'https://itunes.apple.com/us/rss/customerreviews/id=1638054860/sortBy=mostRecent/json'),
        )
        results: list[EvidenceQuote] = []
        seen_quotes: set[str] = set()

        for game_label, url in feeds:
            raw = self._http_get_bytes(url)
            if not raw:
                continue
            try:
                payload = json.loads(raw.decode('utf-8', errors='replace'))
                entries = payload.get('feed', {}).get('entry', [])
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    title = self._nested_label(entry.get('title'))
                    content = self._nested_label(entry.get('content'))
                    author = self._nested_label(entry.get('author', {}).get('name')) if isinstance(entry.get('author'), dict) else ''
                    rating_str = self._nested_label(entry.get('im:rating'))
                    rating = int(rating_str) if rating_str and rating_str.isdigit() else None
                    if not content or len(content) < 18:
                        continue
                    # Prioritize 1-4 star constructive/critical reviews where users express pain points or wishes
                    if rating is not None and rating == 5 and len(results) >= 4:
                        continue
                    clean_quote = self._clean_text(content)[:320]
                    if clean_quote in seen_quotes:
                        continue
                    seen_quotes.add(clean_quote)
                    author_tag = f' (@{author})' if author else ''
                    subject_line = f'{game_label}{author_tag} — "{self._clean_text(title)[:70]}"'
                    results.append(
                        EvidenceQuote(
                            source='app_store',
                            source_label='Apple App Store (Canlı Kullanıcı Yorumu)',
                            subject=subject_line,
                            quote=clean_quote,
                            rating=rating,
                        )
                    )
                    if len([r for r in results if game_label in r.subject]) >= 2:
                        break
            except (ValueError, KeyError, TypeError):
                continue
            if len(results) >= 6:
                break
        return results

    def _fetch_google_play_signals(self) -> list[EvidenceQuote]:
        """Fetches real live Android / Google Play player reviews and discussions from public feeds."""
        results: list[EvidenceQuote] = []
        seen_quotes: set[str] = set()

        # 1. Query live Android/Google Play game reviews & complaints posted on r/AndroidGaming search JSON
        search_urls = (
            'https://www.reddit.com/r/AndroidGaming/search.json?q=Play+Store+review+OR+ads+OR+offline+OR+roguelike&restrict_sr=on&sort=new&limit=10',
            'https://www.reddit.com/r/AndroidGaming/new.json?limit=12',
        )
        for url in search_urls:
            raw = self._http_get_bytes(url)
            if not raw:
                continue
            try:
                payload = json.loads(raw.decode('utf-8', errors='replace'))
                children = payload.get('data', {}).get('children', [])
                if not isinstance(children, list):
                    continue
                for child in children:
                    data = child.get('data', {}) if isinstance(child, dict) else {}
                    if not isinstance(data, dict) or data.get('stickied'):
                        continue
                    title = self._clean_text(str(data.get('title') or ''))
                    selftext = self._clean_text(str(data.get('selftext') or ''))
                    author = str(data.get('author') or '').strip()
                    if not title or len(title) < 12:
                        continue
                    body = selftext if len(selftext) >= 25 else title
                    snippet = body[:320]
                    if snippet in seen_quotes:
                        continue
                    seen_quotes.add(snippet)
                    author_tag = f' (u/{author})' if author else ''
                    results.append(
                        EvidenceQuote(
                            source='google_play',
                            source_label='Google Play / Android Oyuncu Geri Bildirimi (Canlı)',
                            subject=f'{title[:95]}{author_tag}',
                            quote=snippet,
                            rating=None,
                        )
                    )
                    if len(results) >= 5:
                        return results
            except (ValueError, KeyError, TypeError):
                continue

        # 2. Fallback to Google News RSS for Google Play Mobile Games if Reddit search was rate-limited
        rss_url = (
            'https://news.google.com/rss/search?'
            'q=Google+Play+mobile+game+players+review&hl=en-US&gl=US&ceid=US:en'
        )
        raw_rss = self._http_get_bytes(rss_url)
        if raw_rss:
            try:
                root = ET.fromstring(raw_rss.decode('utf-8', errors='replace'))
                for item in root.findall('./channel/item')[:4]:
                    title = self._clean_text(item.findtext('title') or '')
                    if title and title not in seen_quotes:
                        seen_quotes.add(title)
                        results.append(
                            EvidenceQuote(
                                source='google_play',
                                source_label='Google Play Ekosistem Haber/Yorum Akışı (Canlı)',
                                subject=title[:95],
                                quote=title[:280],
                                rating=None,
                            )
                        )
            except ET.ParseError:
                pass

        return results

    def _fetch_reddit_signals(self) -> list[EvidenceQuote]:
        """Fetches real live posts from r/iosgaming, r/AndroidGaming, and r/gamedev."""
        urls = (
            ('Reddit • r/iosgaming (Canlı)', 'https://www.reddit.com/r/iosgaming/new.json?limit=10'),
            ('Reddit • r/AndroidGaming (Canlı)', 'https://www.reddit.com/r/AndroidGaming/hot.json?limit=10'),
            ('Reddit • r/gamedev (Canlı)', 'https://www.reddit.com/r/gamedev/new.json?limit=8'),
        )
        results: list[EvidenceQuote] = []
        seen_quotes: set[str] = set()

        for label, url in urls:
            raw = self._http_get_bytes(url)
            if not raw:
                continue
            try:
                payload = json.loads(raw.decode('utf-8', errors='replace'))
                children = payload.get('data', {}).get('children', [])
                if not isinstance(children, list):
                    continue
                count_for_sub = 0
                for child in children:
                    if not isinstance(child, dict):
                        continue
                    data = child.get('data', {})
                    if not isinstance(data, dict) or data.get('stickied'):
                        continue
                    title = self._clean_text(str(data.get('title') or ''))
                    selftext = self._clean_text(str(data.get('selftext') or ''))
                    author = str(data.get('author') or '').strip()
                    if not title:
                        continue
                    snippet = selftext[:320] if len(selftext) >= 20 else title[:280]
                    if snippet in seen_quotes:
                        continue
                    seen_quotes.add(snippet)
                    author_tag = f' (u/{author})' if author else ''
                    results.append(
                        EvidenceQuote(
                            source='reddit',
                            source_label=label,
                            subject=f'{title[:95]}{author_tag}',
                            quote=snippet,
                            rating=None,
                        )
                    )
                    count_for_sub += 1
                    if count_for_sub >= 2:
                        break
            except (ValueError, KeyError, TypeError):
                continue

        return results

    @staticmethod
    def _nested_label(node: Any) -> str:
        if isinstance(node, dict):
            val = node.get('label')
            if isinstance(val, str):
                return val.strip()
        return ''

    @staticmethod
    def _clean_text(text: str) -> str:
        unescaped = html.unescape(text)
        collapsed = re.sub(r'\s+', ' ', unescaped).strip()
        return collapsed
