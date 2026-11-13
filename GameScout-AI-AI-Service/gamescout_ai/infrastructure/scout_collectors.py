"""Bounded source adapters: original evidence is never rewritten into player claims.

Public feeds are candidates, not guaranteed API access or proof of reuse rights.
Unavailable providers stay unavailable; one platform is never relabelled as another.
"""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import html
import ipaddress
import json
import os
import re
import socket
import ssl
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from gamescout_ai.domain.scout_models import CollectedSignalBatch, EvidenceQuote, SignalCollectorPort

USER_AGENT = 'GameScoutResearch/0.2 (bounded mobile player-needs research)'
HTTP_TIMEOUT_SECONDS = 4.0
MAX_RESPONSE_BYTES = 512 * 1024
MAX_SIGNALS = 80
ALLOWED_HOSTS = frozenset({'itunes.apple.com', 'www.reddit.com'})
# Explicit registry: additions require a reviewed host, rights and data-shape record.
SOURCE_REGISTRY = (
    ('app_store', 'App Store / Stardew Valley', 'https://itunes.apple.com/us/rss/customerreviews/id=1406710800/sortBy=mostRecent/json'),
    ('app_store', 'App Store / Slay the Spire', 'https://itunes.apple.com/us/rss/customerreviews/id=1491530147/sortBy=mostRecent/json'),
    ('reddit', 'r/AndroidGaming player discussions', 'https://www.reddit.com/r/AndroidGaming/new.json?limit=15'),
    ('reddit', 'r/iosgaming player discussions', 'https://www.reddit.com/r/iosgaming/new.json?limit=15'),
    ('reddit', 'r/AndroidGaming request RSS', 'https://www.reddit.com/r/AndroidGaming/new/.rss?limit=15'),
    ('reddit', 'r/iosgaming request RSS', 'https://www.reddit.com/r/iosgaming/new/.rss?limit=15'),
)
REQUEST_TERMS = ('looking for', 'recommend', 'wish', 'want a', 'need a', 'looking to play', 'arıyorum', 'istiyorum', 'keşke', 'öneri')
FEEDBACK_TERMS = REQUEST_TERMS + ('game', 'oyun', 'offline', 'controls', 'monetization', 'strategy', 'puzzle', 'cozy', 'ads', 'rpg', 'mobile', 'android', 'ios')
NOISE_TERMS = ('earnings call', 'stock price', 'geekbench', 'snapdragon benchmark')


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def create_ssl_context() -> ssl.SSLContext:
    paths = ssl.get_default_verify_paths()
    if not paths.cafile and os.path.exists('/etc/ssl/cert.pem'):
        return ssl.create_default_context(cafile='/etc/ssl/cert.pem')
    return ssl.create_default_context()


def is_meaningful_player_feedback(text: str, min_length: int = 30) -> bool:
    lower = text.lower()
    return len(text.strip()) >= min_length and not any(w in lower for w in NOISE_TERMS) and any(w in lower for w in FEEDBACK_TERMS)


def is_turkish_text(text: str) -> bool:
    return bool(re.search('[çğıöşüÇĞİÖŞÜ]', text))


def translate_review_to_turkish(text: str) -> str:
    """Compatibility function: preserve evidence; no translation model was called."""
    return text


def annotate_with_tr_summary_if_english(text: str) -> str:
    return text


def _signal_kind(text: str, default: str = 'discussion') -> str:
    return 'request' if any(term in text.lower() for term in REQUEST_TERMS) else default


def _timestamp(value: Any) -> str | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(value, timezone.utc).isoformat().replace('+00:00', 'Z')
        except (ValueError, OverflowError, OSError):
            return None
    return value if isinstance(value, str) and value.strip() else None


def _evidence(source: str, label: str, subject: str, text: str, url: str | None,
              native_id: str, kind: str, rating: int | None = None,
              published_at: str | None = None, origin: str = 'live') -> EvidenceQuote:
    identity = f'{source}:{native_id or url or ""}:{text}'
    return EvidenceQuote(source=source, source_label=label, subject=subject, quote=text,
                         rating=rating, url=url,
                         evidence_id='ev_' + hashlib.sha256(identity.encode()).hexdigest()[:24],
                         original_text=text, fetched_at=utc_now(), published_at=published_at,
                         signal_kind=kind, data_origin=origin,
                         language='tr' if is_turkish_text(text) else 'unknown', translation_text=None)


_DEMO_REQUESTS = (
    ('request', 'I am looking for an offline mobile puzzle game with short sessions and no forced ads.'),
    ('discussion', 'I enjoy one-handed portrait controls for short mobile strategy sessions during my commute.'),
    ('request', 'I wish mobile co-op games allowed asynchronous turns because my friends play at different times.'),
    ('review', 'Great offline game with no ads and excellent controls. I enjoy its puzzle levels.'),
)
OFFLINE_TEST_SIGNALS = tuple(
    _evidence(source, f'{source} — SENTETİK TEST, gerçek kaynak değildir', f'DEMO player need {index + 1}',
              text, None, f'demo-{source}-{index}', kind, origin='synthetic_demo')
    for source in ('app_store', 'google_play', 'reddit')
    for index, (kind, text) in enumerate(_DEMO_REQUESTS)
)


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_fetch_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def validate_fetch_url(url: str, resolve: bool = True) -> None:
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username
            or parsed.password or parsed.port not in (None, 443)):
        raise ValueError('Source URL is outside the reviewed HTTPS host allowlist')
    if resolve:
        # Fail closed if any returned address is private/local; no arbitrary user URLs.
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError('Source resolved to a non-public address')


class PublicMarketSignalCollector(SignalCollectorPort):
    def __init__(self) -> None:
        self._ssl_ctx = create_ssl_context()
        self._deadline = float('inf')

    def collect_signals(self, allow_network: bool = True) -> CollectedSignalBatch:
        if not allow_network:
            return CollectedSignalBatch(signals=list(OFFLINE_TEST_SIGNALS), live_sources_used=[],
                warnings=['Sentetik test verisi: gerçek oyuncu talebi veya canlı kaynak kapsamı değildir.'],
                data_origin='synthetic_demo', source_statuses={s: 'synthetic_demo' for s in ('app_store', 'google_play', 'reddit')})
        self._deadline = time.monotonic() + 24.0
        signals: list[EvidenceQuote] = []
        statuses: dict[str, str] = {}
        warnings = ['Kaynak örneklemi pazarın tamamını temsil etmez; erişim ve yeniden kullanım hakları ayrıca doğrulanmalıdır.',
                    'Google Play adaptörü doğrulanmadı; Android mağaza yorumu kapsamı mevcut değil.']
        for source, fetch in (('app_store', self._fetch_app_store_signals),
                              ('google_play', self._fetch_google_play_signals),
                              ('reddit', self._fetch_reddit_signals)):
            items = fetch()
            statuses[source] = 'available' if items else 'source_unavailable'
            signals.extend(items)
            if not items and source != 'google_play':
                warnings.append(f'{source}: source_unavailable; veri uydurulmadı veya başka kaynaktan etiketlenmedi.')
        seen: set[str] = set()
        unique = []
        for signal in signals:
            if signal.evidence_id not in seen:
                seen.add(signal.evidence_id)
                unique.append(signal)
        return CollectedSignalBatch(signals=unique[:MAX_SIGNALS],
            live_sources_used=[s for s, status in statuses.items() if status == 'available'],
            warnings=warnings, data_origin='live' if unique else 'no_data', source_statuses=statuses)

    def _http_get_bytes(self, url: str, custom_ua: str | None = None) -> bytes | None:
        if time.monotonic() >= self._deadline:
            return None
        try:
            validate_fetch_url(url)
            request = urllib.request.Request(url, headers={'User-Agent': custom_ua or USER_AGENT,
                'Accept': 'application/json, application/atom+xml, application/rss+xml', 'Accept-Language': 'tr,en;q=0.8'})
            opener = urllib.request.build_opener(SafeRedirectHandler(), urllib.request.HTTPSHandler(context=self._ssl_ctx))
            with opener.open(request, timeout=min(HTTP_TIMEOUT_SECONDS, max(0.1, self._deadline - time.monotonic()))) as response:
                if response.status != 200:
                    return None
                validate_fetch_url(response.geturl())
                body = response.read(MAX_RESPONSE_BYTES + 1)
                return body if len(body) <= MAX_RESPONSE_BYTES else None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return None

    def _fetch_google_play_signals(self) -> list[EvidenceQuote]:
        """No verified/licensed Android review source exists; never substitute Apple."""
        return []

    def _fetch_app_store_signals(self) -> list[EvidenceQuote]:
        results = []
        for source, label, url in SOURCE_REGISTRY:
            if source != 'app_store':
                continue
            raw = self._http_get_bytes(url)
            if not raw:
                continue
            try:
                entries = json.loads(raw.decode('utf-8'))['feed'].get('entry', [])
                for entry in entries[:15] if isinstance(entries, list) else []:
                    if not isinstance(entry, dict):
                        continue
                    content = self._nested_label(entry.get('content'))
                    if not is_meaningful_player_feedback(content):
                        continue
                    rating_raw = self._nested_label(entry.get('im:rating'))
                    rating = int(rating_raw) if rating_raw.isdigit() and 1 <= int(rating_raw) <= 5 else None
                    results.append(_evidence('app_store', label, self._nested_label(entry.get('title')),
                        content, url, self._nested_label(entry.get('id')), 'review', rating,
                        _timestamp(self._nested_label(entry.get('updated')))))
            except (ValueError, KeyError, TypeError, AttributeError):
                continue
        return results

    def _fetch_reddit_signals(self) -> list[EvidenceQuote]:
        results: list[EvidenceQuote] = []
        seen_native_ids: set[str] = set()
        for source, label, url in SOURCE_REGISTRY:
            if source != 'reddit':
                continue
            raw = self._http_get_bytes(url)
            if not raw:
                continue
            try:
                if '/.rss' in url:
                    candidates = self._parse_community_rss(raw, label)
                else:
                    candidates = self._parse_reddit_json(raw, label)
                for item in candidates:
                    # URL/native identity deduplicates JSON and RSS representations of one post.
                    key = item.url or item.evidence_id
                    if key not in seen_native_ids:
                        seen_native_ids.add(key)
                        results.append(item)
            except (ValueError, KeyError, TypeError, AttributeError, ET.ParseError):
                continue
        return results[:40]

    def _parse_reddit_json(self, raw: bytes, label: str) -> list[EvidenceQuote]:
        payload = json.loads(raw.decode('utf-8'))
        children = payload.get('data', {}).get('children', [])
        results = []
        for child in children[:15] if isinstance(children, list) else []:
            data = child.get('data', {}) if isinstance(child, dict) else {}
            if not isinstance(data, dict) or data.get('stickied'):
                continue
            title, content = data.get('title', ''), data.get('selftext', '')
            if not isinstance(title, str) or not isinstance(content, str) or content in ('[removed]', '[deleted]'):
                continue
            text = content if content.strip() else title
            if not is_meaningful_player_feedback(title + ' ' + text):
                continue
            permalink = data.get('permalink')
            if not isinstance(permalink, str) or not permalink.startswith('/r/'):
                continue
            url = 'https://www.reddit.com' + permalink.split('?')[0].rstrip('/') + '/'
            validate_fetch_url(url, resolve=False)
            results.append(_evidence('reddit', label, title, text, url, str(data.get('id', '')),
                _signal_kind(title + ' ' + text), published_at=_timestamp(data.get('created_utc'))))
        return results

    def _parse_community_rss(self, raw: bytes, label: str) -> list[EvidenceQuote]:
        root = ET.fromstring(raw)
        ns = {'a': 'http://www.w3.org/2005/Atom'}
        results = []
        for entry in root.findall('a:entry', ns)[:15]:
            title = entry.findtext('a:title', default='', namespaces=ns)
            body = entry.findtext('a:content', default='', namespaces=ns)
            # HTML-to-text conversion only, never translation or inferred sentiment.
            text = html.unescape(re.sub('<[^>]+>', ' ', body)).strip() or title
            link = entry.find('a:link', ns)
            url = link.get('href') if link is not None else None
            if not url or not is_meaningful_player_feedback(title + ' ' + text):
                continue
            validate_fetch_url(url, resolve=False)
            if urllib.parse.urlsplit(url).hostname != 'www.reddit.com':
                continue
            url = url.split('?')[0].rstrip('/') + '/'
            results.append(_evidence('reddit', label, title, text, url,
                entry.findtext('a:id', default=url, namespaces=ns), _signal_kind(title + ' ' + text),
                published_at=_timestamp(entry.findtext('a:published', default='', namespaces=ns))))
        return results

    @staticmethod
    def _nested_label(node: Any) -> str:
        value = node.get('label') if isinstance(node, dict) else ''
        return value if isinstance(value, str) else ''

    @staticmethod
    def _clean_text(text: str) -> str:
        return text
