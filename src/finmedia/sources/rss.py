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


def fetch_rss(source: dict[str, Any]) -> list[Document]:
    """Download and parse a feed URL."""
    feed = feedparser.parse(source["url"], agent=USER_AGENT)
    if getattr(feed, "bozo", False) and not feed.entries:
        raise ConnectionError(f"{source['id']}: could not read feed ({feed.get('bozo_exception')})")
    return _to_documents(feed, source)
