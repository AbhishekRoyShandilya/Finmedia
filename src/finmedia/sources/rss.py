"""RSS/Atom feed fetcher (regulator press releases and circulars)."""

from __future__ import annotations

import html
import re
from datetime import datetime
from time import mktime
from typing import Any

import feedparser

from ..models import Document

_TAG_RE = re.compile(r"<[^>]+>")
USER_AGENT = "FinmediaResearchBot/0.1 (+research)"


def _clean(text: str) -> str:
    return html.unescape(_TAG_RE.sub(" ", text or "")).strip()


def _to_documents(feed: Any, source: dict[str, Any]) -> list[Document]:
    docs: list[Document] = []
    for entry in feed.entries:
        published = None
        stamp = entry.get("published_parsed") or entry.get("updated_parsed")
        if stamp:
            published = datetime.fromtimestamp(mktime(stamp))
        docs.append(
            Document(
                source_id=source["id"],
                title=_clean(entry.get("title", "")),
                url=entry.get("link", ""),
                text=_clean(entry.get("summary", "") or entry.get("description", "")),
                published_at=published,
                category=source.get("category", ""),
                regulator=source.get("regulator", ""),
            )
        )
    return docs


def parse_feed(raw: str | bytes, source: dict[str, Any]) -> list[Document]:
    """Parse already-downloaded feed content into Documents."""
    return _to_documents(feedparser.parse(raw), source)


BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/126.0 Safari/537.36")


def fetch_rss(source: dict[str, Any]) -> list[Document]:
    """Download (browser-like headers; several Indian sites serve an HTML page to bots) and parse a feed URL."""
    import httpx

    try:
        r = httpx.get(source["url"], timeout=30, follow_redirects=True,
                      headers={"User-Agent": BROWSER_UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    except httpx.HTTPError as exc:
        raise ConnectionError(f"{source['id']}: download failed ({type(exc).__name__}: {exc})") from exc
    if r.status_code >= 400:
        raise ConnectionError(f"{source['id']}: HTTP {r.status_code}")
    raw = r.content.lstrip(b"\xef\xbb\xbf").lstrip()        # a UTF-8 byte-order mark breaks some parsers
    feed = feedparser.parse(raw)
    if not feed.entries:
        # retry with the text decoded by httpx (fixes wrong charset declarations)
        feed = feedparser.parse(r.text.lstrip("﻿").lstrip())
    if getattr(feed, "bozo", False) and not feed.entries:
        raise ConnectionError(f"{source['id']}: could not read feed ({feed.get('bozo_exception')})")
    return _to_documents(feed, source)
