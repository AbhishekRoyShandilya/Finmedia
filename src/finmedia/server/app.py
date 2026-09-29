"""Finmedia web workspace: REST + live event stream (SSE) + the built web app.

    finmedia serve            -> http://127.0.0.1:8020

If FINMEDIA_APP_TOKEN is set, every /api call needs `Authorization: Bearer <token>` (or `?token=` for streams and
links). Keep the server on 127.0.0.1 unless the token is set and you use HTTPS in front of it.
"""

from __future__ import annotations

import asyncio
import json
import os
import queue
import re
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from .. import collectors, memory
from ..agent import objects as ro
from ..agent.tools import registry
from ..ai import AI
from ..config import path_setting, project_root, settings
from ..content import engine as content
from ..content.memo import render_memo
from ..costs import BudgetGuard, month_key
from ..env import get_key, keys_status, load_env
from ..runs import TERMINAL, RunManager
from ..sources import market
from ..store import Store
from ..tools.ptis import PtisBridge


class AskIn(BaseModel):
    question: str
    asof: str | None = None
    depth: str = "standard"


class TextIn(BaseModel):
    text: str


class ContentIn(BaseModel):
    kind: str
    notes: str = ""
    version: int | None = None


class ApproveIn(BaseModel):
    name: str
    role: str
    note: str = ""


class PublishIn(BaseModel):
    url: str = ""


class MemoryIn(BaseModel):
    kind: str
    title: str
    body: str = ""
    tags: list[str] = []
    entities: list[str] = []
    event_date: str | None = None
    status: str = "active"
    supersedes: int | None = None
    author: str = "founder"


class FetchIn(BaseModel):
    url: str


class PlaybookIn(BaseModel):
    topic: str
    asof: str
    sectors: list[str] = []


def _valid_date(s: str | None) -> str | None:
    if s in (None, ""):
        return None
    try:
        return date.fromisoformat(s).isoformat()
    except ValueError as exc:
        raise HTTPException(400, f"bad date {s!r}; use YYYY-MM-DD") from exc


def create_app(store: Store | None = None, provider: str | None = None, start_scheduler: bool = True) -> FastAPI:
    load_env()
    cfg = settings()
    store = store or Store(path_setting("db_path"))
    provider_name = provider or os.environ.get("FINMEDIA_LLM_PROVIDER") or cfg["agent"].get("provider", "anthropic")

    def ai_factory() -> AI:
        return AI(store, cfg, provider_name=provider_name)

    manager = RunManager(store, cfg, ai_factory)
    recovered = manager.recover()
    scheduler = collectors.Scheduler(store, cfg)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):  # type: ignore[no-untyped-def]
        if start_scheduler and cfg.get("collectors", {}).get("enabled", True):
            scheduler.start()
        yield
        scheduler.stop()

    app = FastAPI(title="Finmedia Research Desk", version="0.2.0", lifespan=lifespan)
    app.state.store, app.state.manager, app.state.scheduler = store, manager, scheduler

    @app.middleware("http")
    async def auth(request: Request, call_next):  # type: ignore[no-untyped-def]
        token = get_key("FINMEDIA_APP_TOKEN")
        if token and request.url.path.startswith("/api/"):
            given = request.headers.get("authorization", "").removeprefix("Bearer ").strip() or \
                request.query_params.get("token", "")
            if given != token:
                return JSONResponse({"detail": "unauthorised: set the app token (Settings)"}, status_code=401)
        return await call_next(request)

    def err(exc: Exception, code: int = 400) -> HTTPException:
        return HTTPException(code, str(exc))

    # ------------------------------------------------------------------ status
    @app.get("/api/status")
    def status() -> dict[str, Any]:
        ai = ai_factory()
        bridge = PtisBridge(timeout=3)
        guard = BudgetGuard(store, cfg)
        month = month_key()
        b = cfg["budget"]
        return {
            "ai": ai.status(), "keys": keys_status(),
            "bridge": {"url": bridge.base, "reachable": bridge.reachable()},
            "web_search": market.web_search_provider(),
            "budget": {"month": month, "research_cap_inr": b["research_llm_cap_inr"],
                       "research_spent_inr": round(store.month_spend(month, "llm_research"), 2),
                       "research_left_inr": round(guard.remaining_llm_inr(month, pool="llm_research"), 2),
                       "media_llm_cap_inr": b["llm_cap_inr"], "media_llm_spent_inr": round(store.month_spend(month, "llm"), 2),
                       "monthly_cap_inr": b["monthly_cap_inr"], "total_spent_inr": round(store.month_spend(month), 2)},
            "collectors": {"enabled": bool(cfg.get("collectors", {}).get("enabled", True)),
                           "running": scheduler.thread is not None and scheduler.thread.is_alive(),
                           "last_tick": scheduler.last_tick},
            "memory": memory.counts(store), "depths": cfg["agent"]["depth"], "recovered_runs": recovered,
            "today": date.today().isoformat(),
        }

    @app.get("/api/tools")
    def tools() -> list[dict[str, Any]]:
        bridge_ok = PtisBridge(timeout=3).reachable()
        out = []
        for t in registry():
            why = None
            if t.needs_key and not any(get_key(k) for k in t.needs_key):
                why = f"needs {' or '.join(t.needs_key)}"
            elif t.needs_bridge and not bridge_ok:
                why = "PTIS bridge not running"
            out.append({"name": t.name, "group": t.group, "description": t.description, "available": why is None,
                        "why": why})
        return out

    # ------------------------------------------------------------------ research threads
    @app.get("/api/threads")
    def threads() -> list[dict[str, Any]]:
        return manager.list_threads()

    @app.post("/api/threads")
    def new_thread(body: AskIn) -> dict[str, Any]:
        try:
            return manager.start_research(body.question, asof=_valid_date(body.asof), depth=body.depth)
        except (ValueError, RuntimeError) as exc:
            raise err(exc) from exc

    @app.get("/api/threads/{thread_id}")
    def thread(thread_id: int) -> dict[str, Any]:
        t = manager.get_thread(thread_id)
        if t is None:
            raise HTTPException(404, "no such conversation")
        return t

    @app.delete("/api/threads/{thread_id}")
    def delete_thread(thread_id: int) -> dict[str, Any]:
        try:
            manager.delete_thread(thread_id)
        except RuntimeError as exc:
            raise err(exc) from exc
        return {"ok": True}

    @app.post("/api/threads/{thread_id}/ask")
    def ask(thread_id: int, body: AskIn) -> dict[str, Any]:
        try:
            return manager.start_research(body.question, thread_id=thread_id, asof=_valid_date(body.asof),
                                          depth=body.depth)
        except (ValueError, RuntimeError) as exc:
            raise err(exc) from exc

    @app.get("/api/runs/{run_id}/events")
    def run_events(run_id: int, after: int = 0) -> dict[str, Any]:
        row = store.q1("SELECT status FROM runs WHERE id = ?", (run_id,))
        if row is None:
            raise HTTPException(404, "no such run")
        return {"status": row["status"], "active": manager.is_active(run_id), "events": manager.bus.history(run_id, after)}

    @app.get("/api/runs/{run_id}/stream")
    async def run_stream(run_id: int, request: Request, after: int = 0) -> StreamingResponse:
        if store.q1("SELECT id FROM runs WHERE id = ?", (run_id,)) is None:
            raise HTTPException(404, "no such run")
        q = manager.bus.subscribe(run_id)

        async def gen():  # type: ignore[no-untyped-def]
            try:
                last = after
                for ev in manager.bus.history(run_id, after):
                    last = ev["seq"]
                    yield f"id: {ev['seq']}\nevent: {ev['type']}\ndata: {json.dumps(ev, ensure_ascii=False)}\n\n"
                    if ev["type"] in TERMINAL:
                        return
                while True:
                    if await request.is_disconnected():
                        return
                    try:
                        ev = await asyncio.to_thread(q.get, True, 15)
                    except queue.Empty:
                        yield ": keep-alive\n\n"
                        if not manager.is_active(run_id):
                            return
                        continue
                    if ev["seq"] <= last:
                        continue
                    last = ev["seq"]
                    yield f"id: {ev['seq']}\nevent: {ev['type']}\ndata: {json.dumps(ev, ensure_ascii=False)}\n\n"
                    if ev["type"] in TERMINAL:
                        return
            finally:
                manager.bus.unsubscribe(run_id, q)

        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.post("/api/runs/{run_id}/steer")
    def steer(run_id: int, body: TextIn) -> dict[str, Any]:
        try:
            manager.steer(run_id, body.text)
        except RuntimeError as exc:
            raise err(exc) from exc
        return {"ok": True}

    @app.post("/api/runs/{run_id}/stop")
    def stop(run_id: int) -> dict[str, Any]:
        try:
            manager.stop(run_id)
        except RuntimeError as exc:
            raise err(exc) from exc
        return {"ok": True}

    @app.post("/api/playbooks/budget")
    def playbook(body: PlaybookIn) -> dict[str, Any]:
        try:
            return manager.start_playbook(body.topic, _valid_date(body.asof) or date.today().isoformat(), body.sectors)
        except RuntimeError as exc:
            raise err(exc) from exc

    # ------------------------------------------------------------------ research objects
    @app.get("/api/objects")
    def objects(q: str = "") -> list[dict[str, Any]]:
        return ro.list_objects(store, q)

    @app.get("/api/objects/{key}")
    def get_object(key: str, version: int | None = None) -> dict[str, Any]:
        o = ro.get_object(store, key, version)
        if o is None:
            raise HTTPException(404, "no such Research Object")
        o["claims_rows"] = [dict(r) for r in store.q(
            "SELECT * FROM claims WHERE object_key = ? AND object_version = ? ORDER BY id", (key, o["version"]))]
        o["content"] = content.list_items(store, key=key)
        return o

    @app.get("/api/objects/{key}/memo", response_class=HTMLResponse)
    def memo(key: str, version: int | None = None, edition: str = "internal") -> HTMLResponse:
        o = ro.get_object(store, key, version)
        if o is None:
            raise HTTPException(404, "no such Research Object")
        return HTMLResponse(render_memo(o, internal=edition != "public"))

    @app.post("/api/objects/{key}/content")
    def make_content(key: str, body: ContentIn) -> dict[str, Any]:
        ai = ai_factory()
        if not ai.status()["ready"]:
            raise HTTPException(400, ai.status()["note"])
        try:
            return content.generate(store, ai, key, body.kind, body.notes, body.version)
        except Exception as exc:  # noqa: BLE001
            raise err(exc) from exc

    # ------------------------------------------------------------------ content
    @app.get("/api/content")
    def content_list(status: str | None = None, key: str | None = None) -> list[dict[str, Any]]:
        return content.list_items(store, status, key)

    @app.get("/api/content/{item_id}")
    def content_get(item_id: int) -> dict[str, Any]:
        item = content.get_item(store, item_id)
        if item is None:
            raise HTTPException(404, "no such content item")
        return item

    @app.put("/api/content/{item_id}")
    def content_edit(item_id: int, draft: dict[str, Any] = Body(...)) -> dict[str, Any]:
        try:
            return content.update_draft(store, item_id, draft)
        except Exception as exc:  # noqa: BLE001
            raise err(exc) from exc

    @app.post("/api/content/{item_id}/approve")
    def content_approve(item_id: int, body: ApproveIn) -> dict[str, Any]:
        try:
            return content.approve(store, item_id, body.name, body.role, body.note)
        except content.ContentError as exc:
            raise err(exc) from exc

    @app.post("/api/content/{item_id}/publish")
    def content_publish(item_id: int, body: PublishIn) -> dict[str, Any]:
        try:
            return content.mark_published(store, item_id, body.url)
        except content.ContentError as exc:
            raise err(exc) from exc

    # ------------------------------------------------------------------ memory + documents
    @app.get("/api/memory/search")
    def memory_search(q: str = "", kinds: str = "", asof: str | None = None, tags: str = "",
                      include_superseded: bool = False, limit: int = 50) -> list[dict[str, Any]]:
        return memory.search(store, q, kinds=[k for k in kinds.split(",") if k] or None, asof=_valid_date(asof),
                             tags=[t for t in tags.split(",") if t] or None, limit=min(limit, 200),
                             include_superseded=include_superseded)

    @app.get("/api/memory/timeline")
    def memory_timeline(kinds: str = "", since: str | None = None, until: str | None = None) -> list[dict[str, Any]]:
        return memory.timeline(store, kinds=[k for k in kinds.split(",") if k] or None, since=_valid_date(since),
                               until=_valid_date(until))

    @app.get("/api/memory/{record_id}")
    def memory_get(record_id: int) -> dict[str, Any]:
        r = memory.get(store, record_id)
        if r is None:
            raise HTTPException(404, "no such record")
        r["superseded_by"] = [x["id"] for x in store.q("SELECT id FROM memory_records WHERE supersedes = ?", (record_id,))]
        return r

    @app.post("/api/memory")
    def memory_add(body: MemoryIn) -> dict[str, Any]:
        try:
            rid = memory.add_record(store, body.kind, body.title, body.body, tags=body.tags, entities=body.entities,
                                    event_date=_valid_date(body.event_date), status=body.status,
                                    supersedes=body.supersedes, source_ref="manual", created_by=body.author)
        except ValueError as exc:
            raise err(exc) from exc
        return memory.get(store, rid)

    @app.get("/api/documents")
    def documents(q: str = "", source: str = "", category: str = "", symbol: str = "", limit: int = 50) -> list[dict[str, Any]]:
        return memory.search_documents(store, q, sources=[s for s in source.split(",") if s] or None,
                                       category=category or None, symbol=symbol or None, limit=min(limit, 200))

    @app.get("/api/documents/{doc_id}")
    def document(doc_id: int) -> dict[str, Any]:
        row = store.get_document(doc_id)
        if row is None:
            raise HTTPException(404, "no such document")
        return dict(row)

    @app.post("/api/documents/fetch")
    def fetch_doc(body: FetchIn) -> dict[str, Any]:
        from ..agent.tools import ToolContext, t_fetch_document
        try:
            out = t_fetch_document(ToolContext(store=store, cfg=cfg, asof=date.today().isoformat()),
                                   {"url": body.url, "max_chars": 2000})
        except Exception as exc:  # noqa: BLE001
            raise err(exc) from exc
        return out

    @app.post("/api/inbox")
    async def upload(request: Request, filename: str = Query(...)) -> dict[str, Any]:
        name = re.sub(r"[^\w.\- ]", "_", Path(filename).name)
        if Path(name).suffix.lower() not in (".pdf", ".txt", ".md"):
            raise HTTPException(400, "upload a .pdf, .txt or .md file")
        data = await request.body()
        if len(data) > 40_000_000:
            raise HTTPException(400, "file too large (40 MB max)")
        inbox = path_setting("inbox_dir")
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / name).write_bytes(data)
        src = next(s for s in collectors.sources() if s["id"] == "inbox")
        return {"saved": name, "collect": collectors.run_source(store, src)}

    # ------------------------------------------------------------------ sources / collectors
    @app.get("/api/sources")
    def sources() -> list[dict[str, Any]]:
        return collectors.status(store)

    @app.post("/api/sources/run")
    def run_all() -> list[dict[str, Any]]:
        return collectors.run_due(store, force=True)

    @app.post("/api/sources/{source_id}/run")
    def run_one(source_id: str) -> dict[str, Any]:
        src = next((s for s in collectors.sources() if s["id"] == source_id), None)
        if src is None:
            raise HTTPException(404, "no such source")
        return collectors.run_source(store, src)

    # ------------------------------------------------------------------ claims + scoreboard
    @app.get("/api/claims")
    def claims(limit: int = 500) -> list[dict[str, Any]]:
        rows = []
        for r in store.q("SELECT * FROM claims ORDER BY id DESC LIMIT ?", (limit,)):
            d = dict(r)
            d["outcome"] = json.loads(d.pop("outcome_json") or "null")
            rows.append(d)
        return rows

    @app.get("/api/scoreboard")
    def scoreboard() -> dict[str, Any]:
        rows = [dict(r) for r in store.q("SELECT * FROM claims")]
        scored = []
        for r in rows:
            o = json.loads(r["outcome_json"]) if r["outcome_json"] else None
            if o and o.get("hit") is not None:
                scored.append({**r, "hit": bool(o["hit"]), "abnormal_pct": o.get("abnormal_pct")})

        def group(key: Any) -> list[dict[str, Any]]:
            g: dict[str, list[dict[str, Any]]] = {}
            for s in scored:
                g.setdefault(key(s), []).append(s)
            return sorted(({"group": k, "n": len(v), "hits": sum(x["hit"] for x in v),
                            "hit_rate_pct": round(100 * sum(x["hit"] for x in v) / len(v), 1)} for k, v in g.items()),
                          key=lambda x: -x["n"])

        src = lambda s: ("agent research" if s["source"].startswith("object:") else  # noqa: E731
                         "budget desk CIO" if s["source"] == "cio" else s["source"])
        return {"total_claims": len(rows), "scored": len(scored),
                "pending": sum(1 for r in rows if not r["outcome_json"]),
                "overall": group(lambda s: "all"), "by_source": group(src),
                "by_horizon": group(lambda s: s["horizon"]), "by_confidence": group(lambda s: s["confidence"]),
                "last_postmortem": store.get_state("last_postmortem")}

    @app.post("/api/claims/postmortem")
    def postmortem() -> dict[str, Any]:
        return collectors.score_due_claims(store)

    # ------------------------------------------------------------------ costs
    @app.get("/api/costs")
    def costs(month: str | None = None) -> dict[str, Any]:
        month = month or month_key()
        return {"month": month, "total_inr": round(store.month_spend(month), 2),
                "rows": [dict(r) for r in store.month_breakdown(month)],
                "runs": [dict(r) for r in store.q("SELECT id, thread_id, kind, question, status, cost_inr, started_at "
                                                  "FROM runs WHERE substr(started_at, 1, 7) = ? ORDER BY id DESC", (month,))]}

    @app.get("/api/files")
    def files(path: str) -> FileResponse:
        root = (project_root() / "output").resolve()
        target = (project_root() / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
        if root not in target.parents or not target.is_file():
            raise HTTPException(404, "not found")
        return FileResponse(target)

    # ------------------------------------------------------------------ web app
    dist = project_root() / "web" / "dist"

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):  # type: ignore[no-untyped-def]
        if full_path.startswith("api/"):
            raise HTTPException(404, "unknown API route")
        f = (dist / full_path).resolve()
        if full_path and dist.resolve() in f.parents and f.is_file():
            return FileResponse(f)
        index = dist / "index.html"
        if index.exists():
            return FileResponse(index)
        return HTMLResponse("<h1>Finmedia API is running</h1><p>The web app is not built yet: "
                            "<code>cd web && npm install && npm run build</code></p>")

    return app
