"""Document sources: RSS feeds, GDELT, and a local inbox folder."""

from __future__ import annotations

from typing import Any, Iterable

from ..models import Document
from .gdelt import fetch_gdelt
from .inbox import read_inbox
from .rss import fetch_rss


def fetch_source(source: dict[str, Any], inbox_dir=None) -> Iterable[Document]:
    """Fetch documents for one entry of config/sources.yaml."""
    kind = source["type"]
    if kind == "rss":
        return fetch_rss(source)
    if kind == "gdelt":
        return fetch_gdelt(source)
    if kind == "inbox":
        return read_inbox(inbox_dir, source)
    raise ValueError(f"Unknown source type: {kind!r}")
