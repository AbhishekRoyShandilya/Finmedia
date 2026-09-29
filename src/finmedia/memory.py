"""Research memory: typed, point-in-time, append-only.

Every record carries `known_at` (when we knew it). A search "as of" a date only sees records known by then, so any
study can be re-run as of a past date without leakage. Nothing is overwritten: a correction is a new record whose
`supersedes` points at the old one; the old one then drops out of searches made after the correction.

Similarity uses MECHANISM TAGS (who pays, which channel, proposal vs final...) as well as text, so the desk finds
events that WORK alike, not only ones that sound alike.
"""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from .store import Store, now

KINDS = ("event", "expectation", "reaction", "structure_change", "finding", "note")
FINDING_STATUS = ("hypothesis", "supported", "killed", "superseded")
_WORD = re.compile(r"[\wऀ-ॿ]+", re.UNICODE)


def norm_list(values: Any) -> str:
    if not values:
        return ""
    if isinstance(values, str):
        values = values.split(",")
    return ",".join(sorted({str(v).strip().lower() for v in values if str(v).strip()}))


def add_record(store: Store, kind: str, title: str, body: str = "", *, data: dict[str, Any] | None = None,
               tags: Any = None, entities: Any = None, event_date: str | None = None, known_at: str | None = None,
               status: str = "active", source_ref: str = "manual", supersedes: int | None = None,
               created_by: str = "system") -> int:
    if kind not in KINDS:
        raise ValueError(f"unknown memory kind {kind!r}; use one of {KINDS}")
    if kind == "finding" and status == "active":
        status = "hypothesis"
    if supersedes is not None and store.q1("SELECT 1 FROM memory_records WHERE id = ?", (supersedes,)) is None:
        raise ValueError(f"record {supersedes} does not exist")
    return store.ex(
        """INSERT INTO memory_records (kind, title, body, data_json, tags, entities, event_date, known_at, status,
           source_ref, supersedes, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (kind, title.strip(), body.strip(), json.dumps(data or {}, ensure_ascii=False, default=str), norm_list(tags),
         norm_list(entities), event_date, known_at or now(), status, source_ref, supersedes, created_by))


def _row(r: sqlite3.Row) -> dict[str, Any]:
    d = dict(r)
    d["data"] = json.loads(d.pop("data_json") or "{}")
    d["tags"] = [t for t in (d.get("tags") or "").split(",") if t]
    d["entities"] = [t for t in (d.get("entities") or "").split(",") if t]
    return d


def get(store: Store, record_id: int) -> dict[str, Any] | None:
    r = store.q1("SELECT * FROM memory_records WHERE id = ?", (record_id,))
    return _row(r) if r else None


def fts_query(text: str) -> str:
    words = [w for w in _WORD.findall(text or "") if len(w) > 1][:12]
    return " OR ".join(f'"{w}"' for w in words)


def _asof_bound(asof: str | None) -> str:
    # a bare date means "known by the END of that day"
    if not asof:
        return "9999-12-31T23:59:59"
    return asof + "T23:59:59" if len(asof) == 10 else asof


def search(store: Store, query: str = "", *, kinds: list[str] | None = None, asof: str | None = None,
           tags: list[str] | None = None, entities: list[str] | None = None, status: list[str] | None = None,
           limit: int = 20, include_superseded: bool = False) -> list[dict[str, Any]]:
    bound = _asof_bound(asof)
    where = ["m.known_at <= ?"]
    params: list[Any] = [bound]
    if kinds:
        where.append(f"m.kind IN ({','.join('?' * len(kinds))})")
        params += kinds
    if status:
        where.append(f"m.status IN ({','.join('?' * len(status))})")
        params += status
    for t in [x.strip().lower() for x in (tags or []) if x.strip()]:
        where.append("(',' || m.tags || ',') LIKE ?")
        params.append(f"%,{t},%")
    for e in [x.strip().lower() for x in (entities or []) if x.strip()]:
        where.append("(',' || m.entities || ',') LIKE ?")
        params.append(f"%,{e},%")
    if not include_superseded:
        where.append("m.id NOT IN (SELECT supersedes FROM memory_records WHERE supersedes IS NOT NULL AND known_at <= ?)")
        params.append(bound)
    fq = fts_query(query)
    if fq and store.fts:
        sql = (f"SELECT m.*, bm25(memory_fts) AS score FROM memory_fts JOIN memory_records m ON m.id = memory_fts.rowid "
               f"WHERE memory_fts MATCH ? AND {' AND '.join(where)} ORDER BY score LIMIT ?")
        rows = store.q(sql, [fq, *params, limit])
    else:
        if query.strip():
            where.append("(m.title LIKE ? OR m.body LIKE ?)")
            params += [f"%{query.strip()}%"] * 2
        rows = store.q(f"SELECT m.* FROM memory_records m WHERE {' AND '.join(where)} ORDER BY m.known_at DESC LIMIT ?",
                       [*params, limit])
    return [_row(r) for r in rows]


def similar_by_tags(store: Store, tags: list[str], *, asof: str | None = None, kinds: list[str] | None = None,
                    limit: int = 10) -> list[dict[str, Any]]:
    """Records sharing the most mechanism tags with `tags` (ties broken by recency)."""
    wanted = {t.strip().lower() for t in tags if t.strip()}
    if not wanted:
        return []
    candidates = search(store, "", kinds=kinds, asof=asof, limit=2000)
    scored = []
    for r in candidates:
        overlap = wanted & set(r["tags"])
        if overlap:
            scored.append((len(overlap), r["known_at"], {**r, "shared_tags": sorted(overlap)}))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [r for _, _, r in scored[:limit]]


def timeline(store: Store, *, kinds: list[str] | None = None, since: str | None = None, until: str | None = None,
             limit: int = 200) -> list[dict[str, Any]]:
    where, params = ["1=1"], []
    if kinds:
        where.append(f"kind IN ({','.join('?' * len(kinds))})")
        params += kinds
    if since:
        where.append("COALESCE(event_date, substr(known_at, 1, 10)) >= ?")
        params.append(since)
    if until:
        where.append("COALESCE(event_date, substr(known_at, 1, 10)) <= ?")
        params.append(until)
    rows = store.q(f"SELECT * FROM memory_records WHERE {' AND '.join(where)} "
                   f"ORDER BY COALESCE(event_date, substr(known_at, 1, 10)) DESC, id DESC LIMIT ?", [*params, limit])
    return [_row(r) for r in rows]


def counts(store: Store) -> dict[str, int]:
    out = {k: 0 for k in KINDS}
    for r in store.q("SELECT kind, COUNT(*) AS n FROM memory_records GROUP BY kind"):
        out[r["kind"]] = r["n"]
    out["documents"] = int(store.q1("SELECT COUNT(*) AS n FROM documents")["n"])
    return out


# ------------------------------------------------------------------------------------------------ documents
def search_documents(store: Store, query: str = "", *, asof: str | None = None, sources: list[str] | None = None,
                     category: str | None = None, symbol: str | None = None, since: str | None = None,
                     limit: int = 20) -> list[dict[str, Any]]:
    """Stored documents known by `asof` (fetched_at is our known_at) and, if given, published since `since`."""
    where = ["d.fetched_at <= ?"]
    params: list[Any] = [_asof_bound(asof)]
    if asof:
        where.append("(d.published_at IS NULL OR d.published_at <= ?)")
        params.append(_asof_bound(asof))
    if sources:
        where.append(f"d.source_id IN ({','.join('?' * len(sources))})")
        params += sources
    if category:
        where.append("d.category = ?")
        params.append(category)
    if symbol:
        where.append("UPPER(d.symbol) = ?")
        params.append(symbol.upper())
    if since:
        where.append("COALESCE(d.published_at, d.fetched_at) >= ?")
        params.append(since)
    cols = "d.id, d.source_id, d.title, d.url, d.category, d.regulator, d.published_at, d.fetched_at, d.symbol, d.doc_type, substr(d.text, 1, 400) AS snippet"
    fq = fts_query(query)
    if fq and store.fts:
        rows = store.q(f"SELECT {cols}, bm25(documents_fts) AS score FROM documents_fts JOIN documents d ON d.id = documents_fts.rowid "
                       f"WHERE documents_fts MATCH ? AND {' AND '.join(where)} ORDER BY score LIMIT ?", [fq, *params, limit])
    else:
        if query.strip():
            where.append("(d.title LIKE ? OR d.text LIKE ?)")
            params += [f"%{query.strip()}%"] * 2
        rows = store.q(f"SELECT {cols} FROM documents d WHERE {' AND '.join(where)} "
                       f"ORDER BY COALESCE(d.published_at, d.fetched_at) DESC LIMIT ?", [*params, limit])
    return [dict(r) for r in rows]
