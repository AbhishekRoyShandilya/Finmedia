"""GDELT DOC 2.0 article search, used only to *detect* events.

News articles are signals: the pipeline always goes back to the primary
document before anything is published.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any

from ..models import Document

API = "https://api.gdeltproject.org/api/v2/doc/doc"


def parse_gdelt(payload: dict[str, Any], source: dict[str, Any]) -> list[Document]:
    docs = []
    for art in payload.get("articles", []):
        published = None
        seen = art.get("seendate")  # e.g. 20260926T101500Z
        if seen:
            try:
                published = datetime.strptime(seen, "%Y%m%dT%H%M%SZ")
            except ValueError:
                published = None
        docs.append(
            Document(
                source_id=source["id"],
                title=art.get("title", ""),
                url=art.get("url", ""),
                text=f"{art.get('domain', '')} | {art.get('language', '')}",
                published_at=published,
                category=source.get("category", "news_signal"),
            )
        )
    return docs


def fetch_gdelt(source: dict[str, Any]) -> list[Document]:
    params = {
        "query": source["query"],
        "mode": "artlist",
        "format": "json",
        "maxrecords": str(source.get("max_records", 50)),
        "sort": "datedesc",
    }
    url = f"{API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "FinmediaResearchBot/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8") or "{}")
    return parse_gdelt(payload, source)
