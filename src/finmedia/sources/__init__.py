"""Document sources: RSS feeds, GDELT, the local inbox folder, and NSE filings / calendar."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from ..models import Document
from .gdelt import fetch_gdelt
from .inbox import read_inbox
from .rss import fetch_rss

NSE_TYPES = ("nse_announcements", "nse_calendar")


def _dt(s: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(s) if s else None
    except ValueError:
        return None


def nse_documents(source: dict[str, Any]) -> list[tuple[Document, dict[str, Any]]]:
    """NSE items as (Document, {symbol, doc_type}) pairs."""
    from .market import NSE

    nse = NSE()
    out: list[tuple[Document, dict[str, Any]]] = []
    if source["type"] == "nse_announcements":
        for a in nse.announcements():
            out.append((Document(source_id=source["id"], title=f"{a['symbol']}: {a['subject']}",
                                 url=a.get("attachment") or "", text=a.get("text") or "",
                                 published_at=_dt(a.get("published_at")), category=source.get("category", "filing")),
                        {"symbol": a.get("symbol"), "doc_type": "announcement"}))
    elif source["type"] == "nse_calendar":
        for ev in nse.event_calendar():
            out.append((Document(source_id=source["id"], title=f"{ev['symbol']}: {ev['purpose']} on {ev['date']}",
                                 url="", text=ev.get("details") or "", category=source.get("category", "calendar")),
                        {"symbol": ev.get("symbol"), "doc_type": "calendar"}))
    return out


def fetch_source(source: dict[str, Any], inbox_dir=None) -> Iterable[Document]:
    """Fetch documents for one entry of config/sources.yaml."""
    kind = source["type"]
    if kind == "rss":
        return fetch_rss(source)
    if kind == "gdelt":
        return fetch_gdelt(source)
    if kind == "inbox":
        return read_inbox(inbox_dir, source)
    if kind in NSE_TYPES:
        return [d for d, _ in nse_documents(source)]
    raise ValueError(f"Unknown source type: {kind!r}")
