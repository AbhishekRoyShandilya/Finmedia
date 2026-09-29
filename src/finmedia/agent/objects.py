"""Research Objects: store versions, write their claims and memory updates, flag content built on old versions."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from .. import memory
from ..store import Store, now


def _key_for_thread(store: Store, thread_id: int | None) -> str:
    if thread_id is not None:
        row = store.q1("SELECT object_key FROM threads WHERE id = ?", (thread_id,))
        if row and row["object_key"]:
            return row["object_key"]
        key = f"ro-{thread_id}"
        store.ex("UPDATE threads SET object_key = ? WHERE id = ?", (key, thread_id))
        return key
    n = store.q1("SELECT COUNT(*) AS n FROM research_objects")["n"]
    return f"ro-x{n + 1}"


def save_object(store: Store, obj: dict[str, Any], provenance: dict[str, Any], *, asof: str,
                thread_id: int | None, run_id: int | None, evidence: dict[str, dict[str, Any]]) -> dict[str, Any]:
    key = _key_for_thread(store, thread_id)
    prev = store.q1("SELECT MAX(version) AS v FROM research_objects WHERE key = ?", (key,))
    version = int(prev["v"] or 0) + 1
    status = "final" if provenance.get("ok") else "flagged"
    evidence_index = {r: {"tool": e["tool"], "args": e.get("args"), "ok": e.get("ok"), "at": e.get("at")}
                      for r, e in evidence.items()}
    store.ex("""INSERT INTO research_objects (key, version, thread_id, run_id, title, asof, created_at, status, json,
                provenance_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
             (key, version, thread_id, run_id, obj["title"], asof, now(), status,
              json.dumps(obj, ensure_ascii=False), json.dumps({**provenance, "evidence_index": evidence_index},
                                                              ensure_ascii=False, default=str)))
    # content built from an older version is now stale
    store.ex("UPDATE content_items SET status = 'stale', updated_at = ? WHERE object_key = ? AND object_version < ? "
             "AND status != 'published'", (now(), key, version))

    claims = [dict(target=c["target"], direction=c["direction"], horizon=c["horizon"], confidence=c["confidence"],
                   source=f"object:{key}", object_key=key, object_version=version, rationale=c.get("rationale"),
                   directional=int(c["direction"] in ("positive", "negative")))
              for c in obj.get("claims", [])]
    if claims:
        store.add_claims(0, asof, claims)

    written = 0
    live = asof >= date.today().isoformat()
    if live:                      # a time-travel run must not write "what we knew" into the past
        ref = f"object:{key}@v{version}"
        mu = obj.get("memory_updates") or {}
        for ev in mu.get("events", []):
            memory.add_record(store, "event", ev["title"], ev.get("summary", ""), tags=ev.get("mechanism_tags"),
                              entities=ev.get("entities"), event_date=ev.get("event_date") or None,
                              data={"event_type": ev.get("event_type"), "stage": ev.get("stage"),
                                    "evidence_refs": ev.get("evidence_refs")}, source_ref=ref, created_by="agent")
            written += 1
        for f in mu.get("findings", []):
            memory.add_record(store, "finding", f["statement"], "", tags=f.get("tags"), status=f.get("status", "hypothesis"),
                              data={"review_after": f.get("review_after"), "evidence_refs": f.get("evidence_refs")},
                              source_ref=ref, created_by="agent")
            written += 1
        for s in mu.get("structure_changes", []):
            memory.add_record(store, "structure_change", s["title"], s.get("description", ""), tags=s.get("tags"),
                              entities=s.get("affects"), event_date=s.get("effective_date") or None,
                              data={"affects": s.get("affects"), "evidence_refs": s.get("evidence_refs")},
                              source_ref=ref, created_by="agent")
            written += 1
    return {"key": key, "version": version, "status": status, "claims": len(claims), "memory_written": written,
            "memory_skipped_time_travel": not live}


def _obj_row(r: Any, full: bool = True) -> dict[str, Any]:
    d = {k: r[k] for k in ("id", "key", "version", "thread_id", "run_id", "title", "asof", "created_at", "status")}
    if full:
        d["object"] = json.loads(r["json"])
        d["provenance"] = json.loads(r["provenance_json"])
    return d


def get_object(store: Store, key: str, version: int | None = None) -> dict[str, Any] | None:
    if version is None:
        r = store.q1("SELECT * FROM research_objects WHERE key = ? ORDER BY version DESC LIMIT 1", (key,))
    else:
        r = store.q1("SELECT * FROM research_objects WHERE key = ? AND version = ?", (key, version))
    if r is None:
        return None
    out = _obj_row(r)
    out["versions"] = [v["version"] for v in store.q("SELECT version FROM research_objects WHERE key = ? ORDER BY version", (key,))]
    return out


def list_objects(store: Store, query: str = "", limit: int = 100) -> list[dict[str, Any]]:
    sql = """SELECT o.* FROM research_objects o JOIN (SELECT key, MAX(version) AS v FROM research_objects GROUP BY key) m
             ON m.key = o.key AND m.v = o.version"""
    params: list[Any] = []
    if query.strip():
        sql += " WHERE o.title LIKE ? OR o.json LIKE ?"
        params += [f"%{query.strip()}%"] * 2
    sql += " ORDER BY o.created_at DESC LIMIT ?"
    rows = store.q(sql, [*params, limit])
    out = []
    for r in rows:
        d = _obj_row(r, full=False)
        o = json.loads(r["json"])
        d.update(mode=o.get("mode"), verdict=o.get("verdict"), n_claims=len(o.get("claims", [])),
                 summary=(o.get("executive_summary") or [""])[0])
        out.append(d)
    return out
