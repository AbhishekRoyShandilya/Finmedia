"""SQLite store for documents, triage/brief results and the cost ledger.

SQLite keeps the MVP free to run; the schema mirrors the event object in
docs/intelligence-system-architecture.md so it can move to Postgres later.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from .models import Document

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT UNIQUE NOT NULL,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    text TEXT,
    category TEXT,
    regulator TEXT,
    published_at TEXT,
    fetched_at TEXT NOT NULL,
    prefilter_score INTEGER,
    prefilter_reasons TEXT,
    status TEXT NOT NULL DEFAULT 'new'   -- new | kept | dropped | triaged | briefed
);
CREATE TABLE IF NOT EXISTS triage (
    document_id INTEGER PRIMARY KEY REFERENCES documents(id),
    result_json TEXT NOT NULL,
    materiality INTEGER NOT NULL,
    playbook_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS briefs (
    document_id INTEGER PRIMARY KEY REFERENCES documents(id),
    brief_json TEXT NOT NULL,
    verification_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cost_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,          -- YYYY-MM
    created_at TEXT NOT NULL,
    kind TEXT NOT NULL,           -- llm | subscription | other
    item TEXT NOT NULL,           -- role/model, or subscription name
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    usd REAL DEFAULT 0,
    inr REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS research_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    asof TEXT NOT NULL,             -- the report date; nothing after it was used
    created_at TEXT NOT NULL,
    result_json TEXT NOT NULL,      -- scope, facts, quant pack, personas, skeptic, CIO, verification
    internal_path TEXT,
    public_path TEXT
);
CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES research_runs(id),
    asof TEXT NOT NULL,
    target TEXT NOT NULL,           -- sector:<name> or stock:<sym>
    direction TEXT NOT NULL,        -- positive | negative | neutral | mixed
    horizon TEXT NOT NULL,
    confidence TEXT NOT NULL,
    source TEXT NOT NULL,           -- cio | persona:<name>
    outcome_json TEXT               -- filled by research-postmortem
);
"""


class Store:
    def __init__(self, db_path: Path | str):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # The research desk runs its persona panel in threads; they share this connection under one lock.
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.lock = threading.RLock()
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    # ----------------------------------------------------------- documents

    def add_document(self, doc: Document) -> int | None:
        """Insert a document; return its id, or None if it is a duplicate."""
        try:
            cur = self.conn.execute(
                """INSERT INTO documents (content_hash, source_id, title, url, text,
                   category, regulator, published_at, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc.content_hash,
                    doc.source_id,
                    doc.title,
                    doc.url,
                    doc.text,
                    doc.category,
                    doc.regulator,
                    doc.published_at.isoformat() if doc.published_at else None,
                    doc.fetched_at.isoformat(),
                ),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None

    def documents(self, status: str | None = None, limit: int | None = None) -> Iterator[sqlite3.Row]:
        sql = "SELECT * FROM documents"
        params: list[Any] = []
        if status:
            sql += " WHERE status = ?"
            params.append(status)
        sql += " ORDER BY id"
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        yield from self.conn.execute(sql, params)

    def get_document(self, doc_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()

    def set_prefilter(self, doc_id: int, score: int, reasons: list[str], kept: bool) -> None:
        self.conn.execute(
            "UPDATE documents SET prefilter_score = ?, prefilter_reasons = ?, status = ? WHERE id = ?",
            (score, json.dumps(reasons, ensure_ascii=False), "kept" if kept else "dropped", doc_id),
        )
        self.conn.commit()

    def set_status(self, doc_id: int, status: str) -> None:
        self.conn.execute("UPDATE documents SET status = ? WHERE id = ?", (status, doc_id))
        self.conn.commit()

    # -------------------------------------------------------- triage/briefs

    def save_triage(self, doc_id: int, result: dict[str, Any]) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO triage (document_id, result_json, materiality, playbook_id, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                doc_id,
                json.dumps(result, ensure_ascii=False),
                int(result["materiality"]),
                result["playbook_id"],
                datetime.now().isoformat(),
            ),
        )
        self.set_status(doc_id, "triaged")

    def get_triage(self, doc_id: int) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT result_json FROM triage WHERE document_id = ?", (doc_id,)).fetchone()
        return json.loads(row["result_json"]) if row else None

    def top_triaged(self, min_materiality: int, limit: int) -> list[sqlite3.Row]:
        return list(
            self.conn.execute(
                """SELECT d.*, t.materiality, t.playbook_id FROM documents d
                   JOIN triage t ON t.document_id = d.id
                   WHERE d.status = 'triaged' AND t.materiality >= ?
                   ORDER BY t.materiality DESC LIMIT ?""",
                (min_materiality, limit),
            )
        )

    def save_brief(self, doc_id: int, brief: dict[str, Any], verification: dict[str, Any]) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO briefs (document_id, brief_json, verification_json, created_at)
               VALUES (?, ?, ?, ?)""",
            (
                doc_id,
                json.dumps(brief, ensure_ascii=False),
                json.dumps(verification, ensure_ascii=False),
                datetime.now().isoformat(),
            ),
        )
        self.set_status(doc_id, "briefed")

    def get_brief(self, doc_id: int) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT brief_json FROM briefs WHERE document_id = ?", (doc_id,)).fetchone()
        return json.loads(row["brief_json"]) if row else None

    # ------------------------------------------------------ research desk

    def save_research_run(self, topic: str, asof: str, result: dict[str, Any],
                          internal_path: str | None, public_path: str | None) -> int:
        cur = self.conn.execute(
            """INSERT INTO research_runs (topic, asof, created_at, result_json, internal_path, public_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (topic, asof, datetime.now().isoformat(), json.dumps(result, ensure_ascii=False, default=str),
             internal_path, public_path),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def add_claims(self, run_id: int, asof: str, rows: list[dict[str, Any]]) -> None:
        self.conn.executemany(
            """INSERT INTO claims (run_id, asof, target, direction, horizon, confidence, source)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [(run_id, asof, r["target"], r["direction"], r["horizon"], r["confidence"], r["source"]) for r in rows],
        )
        self.conn.commit()

    def claims(self, unscored_only: bool = False) -> list[sqlite3.Row]:
        sql = "SELECT * FROM claims" + (" WHERE outcome_json IS NULL" if unscored_only else "") + " ORDER BY id"
        return list(self.conn.execute(sql))

    def set_claim_outcome(self, claim_id: int, outcome: dict[str, Any]) -> None:
        self.conn.execute("UPDATE claims SET outcome_json = ? WHERE id = ?",
                          (json.dumps(outcome, ensure_ascii=False, default=str), claim_id))
        self.conn.commit()

    # --------------------------------------------------------- cost ledger

    def add_cost(self, *, month: str, kind: str, item: str, inr: float, usd: float = 0.0,
                 input_tokens: int = 0, output_tokens: int = 0,
                 cache_write_tokens: int = 0, cache_read_tokens: int = 0) -> None:
        with self.lock:
            self._add_cost(month, kind, item, inr, usd, input_tokens, output_tokens, cache_write_tokens,
                           cache_read_tokens)

    def _add_cost(self, month, kind, item, inr, usd, input_tokens, output_tokens, cache_write_tokens,
                  cache_read_tokens) -> None:
        self.conn.execute(
            """INSERT INTO cost_ledger (month, created_at, kind, item, input_tokens, output_tokens,
               cache_write_tokens, cache_read_tokens, usd, inr)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (month, datetime.now().isoformat(), kind, item, input_tokens, output_tokens,
             cache_write_tokens, cache_read_tokens, usd, inr),
        )
        self.conn.commit()

    def month_spend(self, month: str, kind: str | None = None) -> float:
        sql = "SELECT COALESCE(SUM(inr), 0) AS total FROM cost_ledger WHERE month = ?"
        params: list[Any] = [month]
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        with self.lock:
            return float(self.conn.execute(sql, params).fetchone()["total"])

    def month_breakdown(self, month: str) -> list[sqlite3.Row]:
        return list(
            self.conn.execute(
                """SELECT kind, item, COUNT(*) AS calls, SUM(input_tokens) AS input_tokens,
                          SUM(output_tokens) AS output_tokens, SUM(inr) AS inr
                   FROM cost_ledger WHERE month = ? GROUP BY kind, item ORDER BY inr DESC""",
                (month,),
            )
        )
