"""SQLite store: documents, triage/briefs, the cost ledger, the research desk, and the workspace (research memory,
conversations, runs, Research Objects, content, collectors).

SQLite keeps it free to run; the schema mirrors docs/research-desk-architecture.md so it can move to Postgres later.
The web server, collectors and research runs share one connection from several threads, so EVERY statement goes
through `self.lock`.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
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
    fetched_at TEXT NOT NULL,          -- = known_at: when WE first had it
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
    kind TEXT NOT NULL,           -- llm | llm_research | subscription | other
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
    run_id INTEGER NOT NULL,        -- research_runs.id (budget playbook) or 0 for agent Research Objects
    asof TEXT NOT NULL,
    target TEXT NOT NULL,           -- sector:<name> or stock:<sym> or index/macro:<name>
    direction TEXT NOT NULL,        -- positive | negative | neutral | mixed
    horizon TEXT NOT NULL,
    confidence TEXT NOT NULL,
    source TEXT NOT NULL,           -- cio | persona:<name> | object:<key>
    outcome_json TEXT               -- filled by research-postmortem
);

-- ------------------------------------------------------------------ workspace
CREATE TABLE IF NOT EXISTS memory_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,             -- event | expectation | reaction | structure_change | finding | note
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    data_json TEXT NOT NULL DEFAULT '{}',
    tags TEXT NOT NULL DEFAULT '',          -- mechanism tags, comma separated, lower case
    entities TEXT NOT NULL DEFAULT '',      -- symbols / sectors / institutions, comma separated
    event_date TEXT,                        -- when it happened / takes effect (may be NULL)
    known_at TEXT NOT NULL,                 -- when we knew it (point-in-time key)
    status TEXT NOT NULL DEFAULT 'active',  -- findings: hypothesis | supported | killed ; others: active
    source_ref TEXT NOT NULL DEFAULT '',    -- object:<key>@v<n> | manual | collector:<id>
    supersedes INTEGER,                     -- id of the record this one corrects (append-only corrections)
    created_by TEXT NOT NULL DEFAULT 'system'
);
CREATE INDEX IF NOT EXISTS ix_memory_kind ON memory_records(kind, known_at);
CREATE TABLE IF NOT EXISTS threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    asof TEXT,
    object_key TEXT
);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER,
    kind TEXT NOT NULL,             -- research | playbook | content
    question TEXT NOT NULL,
    status TEXT NOT NULL,           -- queued | running | done | failed | stopped
    depth TEXT,
    asof TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    cost_inr REAL NOT NULL DEFAULT 0,
    error TEXT,
    messages_json TEXT NOT NULL DEFAULT '[]',
    tool_log_json TEXT NOT NULL DEFAULT '[]',
    result_json TEXT
);
CREATE TABLE IF NOT EXISTS run_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    seq INTEGER NOT NULL,
    ts TEXT NOT NULL,
    type TEXT NOT NULL,
    data_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_run_events ON run_events(run_id, seq);
CREATE TABLE IF NOT EXISTS research_objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,
    version INTEGER NOT NULL,
    thread_id INTEGER,
    run_id INTEGER,
    title TEXT NOT NULL,
    asof TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'final',   -- final | flagged (provenance problems left after one revision)
    json TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    UNIQUE(key, version)
);
CREATE TABLE IF NOT EXISTS content_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_key TEXT NOT NULL,
    object_version INTEGER NOT NULL,
    kind TEXT NOT NULL,             -- reel | youtube | carousel | newsletter | memo
    title TEXT NOT NULL,
    status TEXT NOT NULL,           -- draft | approved | published | stale
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    json TEXT NOT NULL,
    lint_json TEXT NOT NULL,
    approvals_json TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS collector_state (
    source_id TEXT PRIMARY KEY,
    last_run TEXT,
    last_ok TEXT,
    last_error TEXT,
    fail_streak INTEGER NOT NULL DEFAULT 0,
    fetched_total INTEGER NOT NULL DEFAULT 0,
    new_total INTEGER NOT NULL DEFAULT 0,
    last_new INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS app_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(title, text, content='documents', content_rowid='id');
CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(title, body, tags, entities, content='memory_records', content_rowid='id');
CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
  INSERT INTO documents_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;
CREATE TRIGGER IF NOT EXISTS memory_ai AFTER INSERT ON memory_records BEGIN
  INSERT INTO memory_fts(rowid, title, body, tags, entities) VALUES (new.id, new.title, new.body, new.tags, new.entities);
END;
"""

# Columns added after the first release (ALTER TABLE ... ADD COLUMN when missing).
MIGRATIONS = {
    "documents": {"symbol": "TEXT", "doc_type": "TEXT", "meta_json": "TEXT"},
    "claims": {"object_key": "TEXT", "object_version": "INTEGER", "rationale": "TEXT", "directional": "INTEGER DEFAULT 1"},
}


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Store:
    def __init__(self, db_path: Path | str):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
        self.lock = threading.RLock()
        self.conn.row_factory = sqlite3.Row
        with self.lock:
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.executescript(SCHEMA)
            self._migrate()
            self.fts = self._init_fts()

    def _migrate(self) -> None:
        for table, cols in MIGRATIONS.items():
            have = {r["name"] for r in self.conn.execute(f"PRAGMA table_info({table})")}
            for col, decl in cols.items():
                if col not in have:
                    self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
        self.conn.commit()

    def _init_fts(self) -> bool:
        try:
            fresh = not self.conn.execute(
                "SELECT 1 FROM sqlite_master WHERE name='documents_fts'").fetchone()
            self.conn.executescript(FTS_SCHEMA)
            if fresh:     # index rows that existed before full-text search was added
                self.conn.execute("INSERT INTO documents_fts(documents_fts) VALUES ('rebuild')")
                self.conn.execute("INSERT INTO memory_fts(memory_fts) VALUES ('rebuild')")
            self.conn.commit()
            return True
        except sqlite3.OperationalError:
            return False      # SQLite built without FTS5: search falls back to LIKE

    def close(self) -> None:
        with self.lock:
            self.conn.close()

    # ------------------------------------------------------------- helpers
    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        with self.lock:
            try:
                yield self.conn
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

    def q(self, sql: str, params: tuple | list = ()) -> list[sqlite3.Row]:
        with self.lock:
            return list(self.conn.execute(sql, params))

    def q1(self, sql: str, params: tuple | list = ()) -> sqlite3.Row | None:
        with self.lock:
            return self.conn.execute(sql, params).fetchone()

    def ex(self, sql: str, params: tuple | list = ()) -> int:
        with self.tx() as c:
            return int(c.execute(sql, params).lastrowid or 0)

    def get_state(self, key: str, default: str | None = None) -> str | None:
        row = self.q1("SELECT value FROM app_state WHERE key = ?", (key,))
        return row["value"] if row else default

    def set_state(self, key: str, value: str) -> None:
        self.ex("INSERT INTO app_state(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value))

    # ----------------------------------------------------------- documents

    def add_document(self, doc: Document, symbol: str | None = None, doc_type: str | None = None,
                     meta: dict[str, Any] | None = None) -> int | None:
        """Insert a document; return its id, or None if it is a duplicate."""
        try:
            return self.ex(
                """INSERT INTO documents (content_hash, source_id, title, url, text, category, regulator,
                   published_at, fetched_at, symbol, doc_type, meta_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (doc.content_hash, doc.source_id, doc.title, doc.url, doc.text, doc.category, doc.regulator,
                 doc.published_at.isoformat() if doc.published_at else None, doc.fetched_at.isoformat(),
                 symbol, doc_type, json.dumps(meta, ensure_ascii=False, default=str) if meta else None))
        except sqlite3.IntegrityError:
            return None

    def find_document_by_hash(self, content_hash: str) -> sqlite3.Row | None:
        return self.q1("SELECT * FROM documents WHERE content_hash = ?", (content_hash,))

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
        yield from self.q(sql, params)

    def get_document(self, doc_id: int) -> sqlite3.Row | None:
        return self.q1("SELECT * FROM documents WHERE id = ?", (doc_id,))

    def set_prefilter(self, doc_id: int, score: int, reasons: list[str], kept: bool) -> None:
        self.ex("UPDATE documents SET prefilter_score = ?, prefilter_reasons = ?, status = ? WHERE id = ?",
                (score, json.dumps(reasons, ensure_ascii=False), "kept" if kept else "dropped", doc_id))

    def set_status(self, doc_id: int, status: str) -> None:
        self.ex("UPDATE documents SET status = ? WHERE id = ?", (status, doc_id))

    # -------------------------------------------------------- triage/briefs

    def save_triage(self, doc_id: int, result: dict[str, Any]) -> None:
        self.ex("""INSERT OR REPLACE INTO triage (document_id, result_json, materiality, playbook_id, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (doc_id, json.dumps(result, ensure_ascii=False), int(result["materiality"]), result["playbook_id"],
                 datetime.now().isoformat()))
        self.set_status(doc_id, "triaged")

    def get_triage(self, doc_id: int) -> dict[str, Any] | None:
        row = self.q1("SELECT result_json FROM triage WHERE document_id = ?", (doc_id,))
        return json.loads(row["result_json"]) if row else None

    def top_triaged(self, min_materiality: int, limit: int) -> list[sqlite3.Row]:
        return self.q("""SELECT d.*, t.materiality, t.playbook_id FROM documents d
                         JOIN triage t ON t.document_id = d.id
                         WHERE d.status = 'triaged' AND t.materiality >= ?
                         ORDER BY t.materiality DESC LIMIT ?""", (min_materiality, limit))

    def save_brief(self, doc_id: int, brief: dict[str, Any], verification: dict[str, Any]) -> None:
        self.ex("""INSERT OR REPLACE INTO briefs (document_id, brief_json, verification_json, created_at)
                   VALUES (?, ?, ?, ?)""",
                (doc_id, json.dumps(brief, ensure_ascii=False), json.dumps(verification, ensure_ascii=False),
                 datetime.now().isoformat()))
        self.set_status(doc_id, "briefed")

    def get_brief(self, doc_id: int) -> dict[str, Any] | None:
        row = self.q1("SELECT brief_json FROM briefs WHERE document_id = ?", (doc_id,))
        return json.loads(row["brief_json"]) if row else None

    # ------------------------------------------------------ research desk

    def save_research_run(self, topic: str, asof: str, result: dict[str, Any],
                          internal_path: str | None, public_path: str | None) -> int:
        return self.ex("""INSERT INTO research_runs (topic, asof, created_at, result_json, internal_path, public_path)
                          VALUES (?, ?, ?, ?, ?, ?)""",
                       (topic, asof, datetime.now().isoformat(), json.dumps(result, ensure_ascii=False, default=str),
                        internal_path, public_path))

    def add_claims(self, run_id: int, asof: str, rows: list[dict[str, Any]]) -> None:
        with self.tx() as c:
            c.executemany(
                """INSERT INTO claims (run_id, asof, target, direction, horizon, confidence, source, object_key,
                   object_version, rationale, directional) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [(run_id, asof, r["target"], r["direction"], r["horizon"], r["confidence"], r["source"],
                  r.get("object_key"), r.get("object_version"), r.get("rationale"), int(r.get("directional", 1)))
                 for r in rows])

    def claims(self, unscored_only: bool = False) -> list[sqlite3.Row]:
        sql = "SELECT * FROM claims" + (" WHERE outcome_json IS NULL" if unscored_only else "") + " ORDER BY id"
        return self.q(sql)

    def set_claim_outcome(self, claim_id: int, outcome: dict[str, Any]) -> None:
        self.ex("UPDATE claims SET outcome_json = ? WHERE id = ?",
                (json.dumps(outcome, ensure_ascii=False, default=str), claim_id))

    # --------------------------------------------------------- cost ledger

    def add_cost(self, *, month: str, kind: str, item: str, inr: float, usd: float = 0.0,
                 input_tokens: int = 0, output_tokens: int = 0,
                 cache_write_tokens: int = 0, cache_read_tokens: int = 0) -> None:
        self.ex("""INSERT INTO cost_ledger (month, created_at, kind, item, input_tokens, output_tokens,
                   cache_write_tokens, cache_read_tokens, usd, inr) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (month, datetime.now().isoformat(), kind, item, input_tokens, output_tokens,
                 cache_write_tokens, cache_read_tokens, usd, inr))

    def month_spend(self, month: str, kind: str | None = None) -> float:
        sql = "SELECT COALESCE(SUM(inr), 0) AS total FROM cost_ledger WHERE month = ?"
        params: list[Any] = [month]
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        return float(self.q1(sql, params)["total"])

    def month_breakdown(self, month: str) -> list[sqlite3.Row]:
        return self.q("""SELECT kind, item, COUNT(*) AS calls, SUM(input_tokens) AS input_tokens,
                         SUM(output_tokens) AS output_tokens, SUM(inr) AS inr
                         FROM cost_ledger WHERE month = ? GROUP BY kind, item ORDER BY inr DESC""", (month,))
