"""The research agent's tools. Each tool: a name, a description the model reads, a JSON schema, and a handler.

Every call is logged as evidence under a ref (E1, E2, ...). The Research Object may only use numbers and sources that
came back in that evidence (see provenance.py). Tools honour the run's `asof` date: nothing published after it is
returned, and tools that cannot guarantee that say so in `pit_warning`.
"""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Callable

import yaml

from .. import memory
from ..config import load_yaml, project_root
from ..env import get_key
from ..models import Document
from ..sources import market
from ..sources.rss import fetch_rss
from ..store import Store
from ..tools.ptis import BridgeError, PtisBridge
from .models import PanelNote, RedTeamReview, ResearchObject
from .provenance import allowed_from_evidence, numbers_in_text
from ..research.verify import _supported
from ..ai.providers import ToolSpec, inline_refs


class ToolFailure(RuntimeError):
    """A tool could not do its job; the message goes back to the model as an error result."""


@dataclass
class ToolContext:
    store: Store
    cfg: dict[str, Any]
    asof: str                                   # report date (YYYY-MM-DD); today for live research
    ai: Any = None                              # finmedia.ai.AI (panel, red team, playbooks)
    bridge: PtisBridge | None = None
    nse: market.NSE | None = None
    question: str = ""
    run_id: int | None = None
    evidence: dict[str, dict[str, Any]] = field(default_factory=dict)
    cost_inr: float = 0.0
    emit: Callable[[str, dict[str, Any]], None] = lambda t, d: None
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _n: int = 0

    @property
    def live(self) -> bool:
        return self.asof >= date.today().isoformat()

    def next_ref(self) -> str:
        with self._lock:
            self._n += 1
            return f"E{self._n}"

    def add_cost(self, inr: float) -> None:
        with self._lock:
            self.cost_inr += inr

    def seed_refs(self, n: int) -> None:
        """Continue numbering after an earlier run in the same conversation."""
        self._n = max(self._n, n)


@dataclass
class Tool:
    name: str
    description: str
    params: dict[str, Any]
    required: list[str]
    handler: Callable[[ToolContext, dict[str, Any]], Any]
    group: str
    needs_key: tuple[str, ...] = ()
    needs_bridge: bool = False
    needs_ai: bool = False

    def spec(self) -> ToolSpec:
        schema = {"type": "object", "properties": self.params, "required": self.required,
                  "additionalProperties": False}
        return ToolSpec(self.name, self.description, schema)


def _s(desc: str, **kw: Any) -> dict[str, Any]:
    return {"type": "string", "description": desc, **kw}


def _i(desc: str, default: int | None = None, **kw: Any) -> dict[str, Any]:
    d: dict[str, Any] = {"type": "integer", "description": desc, **kw}
    if default is not None:
        d["description"] += f" (default {default})"
    return d


def _arr(desc: str, item: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"type": "array", "items": item or {"type": "string"}, "description": desc}


def _limit(args: dict[str, Any], default: int, hi: int = 50) -> int:
    try:
        return max(1, min(int(args.get("limit") or default), hi))
    except (TypeError, ValueError):
        return default


def _before(ts: str | None, asof: str) -> bool:
    return not ts or ts[:10] <= asof


# =============================================================================================== memory tools
def t_memory_search(ctx: ToolContext, a: dict[str, Any]) -> Any:
    rows = memory.search(ctx.store, a.get("query", ""), kinds=a.get("kinds") or None, asof=ctx.asof,
                         tags=a.get("tags") or None, entities=a.get("entities") or None, limit=_limit(a, 10, 30))
    return {"records": [{k: r[k] for k in ("id", "kind", "title", "body", "tags", "entities", "event_date", "known_at",
                                           "status", "source_ref", "data")} for r in rows]}


def t_memory_similar(ctx: ToolContext, a: dict[str, Any]) -> Any:
    rows = memory.similar_by_tags(ctx.store, a.get("tags") or [], asof=ctx.asof, kinds=a.get("kinds") or None,
                                  limit=_limit(a, 10, 30))
    return {"records": [{k: r[k] for k in ("id", "kind", "title", "body", "tags", "event_date", "known_at", "status",
                                           "shared_tags")} for r in rows]}


def t_documents_search(ctx: ToolContext, a: dict[str, Any]) -> Any:
    rows = memory.search_documents(ctx.store, a.get("query", ""), asof=ctx.asof, sources=a.get("sources") or None,
                                   category=a.get("category") or None, symbol=a.get("symbol") or None,
                                   since=a.get("since") or None, limit=_limit(a, 10, 30))
    return {"documents": rows}


def t_read_stored_document(ctx: ToolContext, a: dict[str, Any]) -> Any:
    row = ctx.store.get_document(int(a["doc_id"]))
    if row is None:
        raise ToolFailure(f"no stored document {a['doc_id']}")
    if not _before(row["fetched_at"], ctx.asof):
        raise ToolFailure("that document was collected after the report date")
    text = row["text"] or ""
    off = max(0, int(a.get("offset") or 0))
    n = max(500, min(int(a.get("max_chars") or 12000), 40000))
    return {"doc_id": row["id"], "title": row["title"], "url": row["url"], "published_at": row["published_at"],
            "total_chars": len(text), "offset": off, "text": text[off:off + n],
            "more": off + n < len(text)}


# ======================================================================================== primary sources
FEEDS = {"rbi": ["rbi_press_releases", "rbi_notifications"], "sebi": ["sebi_rss"], "pib": ["pib_releases"],
         "fed": ["fed_press_all", "fed_monetary"]}


def _source_cfg() -> dict[str, dict[str, Any]]:
    return {s["id"]: s for s in load_yaml("config/sources.yaml")["sources"]}


def t_regulator_feed(ctx: ToolContext, a: dict[str, Any]) -> Any:
    which = a.get("source", "rbi")
    ids = FEEDS.get(which)
    if not ids:
        raise ToolFailure(f"source must be one of {sorted(FEEDS)}")
    notes = []
    if ctx.live:
        cfgs = _source_cfg()
        for sid in ids:
            if sid in cfgs:
                try:
                    for d in fetch_rss(cfgs[sid]):
                        ctx.store.add_document(d, doc_type="release")
                except Exception as exc:  # noqa: BLE001
                    notes.append(f"live fetch of {sid} failed: {exc}; showing stored items")
    else:
        notes.append("time-travel run: showing only items we had stored by the report date")
    since = (date.fromisoformat(ctx.asof) - timedelta(days=int(a.get("days") or 30))).isoformat()
    rows = memory.search_documents(ctx.store, a.get("query", ""), asof=ctx.asof, sources=ids, since=since,
                                   limit=_limit(a, 15, 40))
    return {"source": which, "items": rows, "notes": notes}


def _nse(ctx: ToolContext) -> market.NSE:
    if ctx.nse is None:
        ctx.nse = market.NSE()
    return ctx.nse


def _match(q: str, *texts: Any) -> bool:
    if not q:
        return True
    words = [w.lower() for w in q.split() if len(w) > 2]
    blob = " ".join(str(t or "") for t in texts).lower()
    return all(w in blob for w in words)


def t_nse_announcements(ctx: ToolContext, a: dict[str, Any]) -> Any:
    to_date = min(a.get("to_date") or ctx.asof, ctx.asof)
    from_date = a.get("from_date") or ((date.fromisoformat(to_date) - timedelta(days=30)).isoformat()
                                       if a.get("symbol") or not ctx.live else None)
    rows = _nse(ctx).announcements(a.get("symbol"), from_date, to_date if from_date else None)
    rows = [r for r in rows if _before(r["published_at"], ctx.asof) and _match(a.get("query", ""), r["subject"], r["text"])]
    for r in rows[:40]:
        ctx.store.add_document(Document(source_id="nse_announcements", title=f"{r['symbol']}: {r['subject']}",
                                        url=r.get("attachment") or "", text=r.get("text") or "",
                                        published_at=_dt(r["published_at"]), category="filing"),
                               symbol=r.get("symbol"), doc_type="announcement")
    return {"announcements": rows[:_limit(a, 15, 50)],
            "note": "Without a symbol NSE returns only its latest ~20 filings. Read an attachment with fetch_document."}


def t_nse_results(ctx: ToolContext, a: dict[str, Any]) -> Any:
    rows = [r for r in _nse(ctx).financial_results(a["symbol"]) if _before(r["published_at"], ctx.asof)]
    return {"results": rows[:_limit(a, 8, 30)],
            "note": "Pass a row's xbrl link to nse_result_figures for the reported numbers."}


def t_nse_result_figures(ctx: ToolContext, a: dict[str, Any]) -> Any:
    return market.xbrl_financials(a["xbrl_url"])


def t_nse_event_calendar(ctx: ToolContext, a: dict[str, Any]) -> Any:
    rows = _nse(ctx).event_calendar(a.get("symbol"))
    if not a.get("symbol"):
        rows = [r for r in rows if (r["date"] or "") >= ctx.asof]
    rows.sort(key=lambda r: r["date"] or "", reverse=bool(a.get("symbol")))
    out = {"events": rows[:_limit(a, 20, 60)]}
    if not ctx.live:
        out["pit_warning"] = "NSE's calendar is today's view; for a past report date it may include later announcements."
    return out


def t_nse_corporate_actions(ctx: ToolContext, a: dict[str, Any]) -> Any:
    rows = [r for r in _nse(ctx).corporate_actions(a.get("symbol")) if _before(r["ex_date"], ctx.asof) or ctx.live]
    return {"actions": rows[:_limit(a, 20, 50)]}


def t_nse_shareholding(ctx: ToolContext, a: dict[str, Any]) -> Any:
    rows = [r for r in _nse(ctx).shareholding(a["symbol"]) if _before(r["published_at"], ctx.asof)]
    return {"shareholding": rows[:_limit(a, 8, 20)],
            "note": "Promoter/public % by quarter; the xbrl link has the full pattern (FII, DII, retail)."}


def _dt(s: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(s) if s else None
    except ValueError:
        return None


def t_fetch_document(ctx: ToolContext, a: dict[str, Any]) -> Any:
    url = a["url"].strip()
    existing = ctx.store.q1("SELECT * FROM documents WHERE url = ? AND source_id = 'fetched' ORDER BY id DESC LIMIT 1", (url,))
    if existing is not None:
        doc_id, title, text, kind, pages = existing["id"], existing["title"], existing["text"] or "", existing["doc_type"], None
    else:
        got = market.fetch_url_text(url)
        text, title, kind, pages = got["text"], got["title"], got["kind"], got["pages"]
        doc_id = ctx.store.add_document(Document(source_id="fetched", title=title[:300], url=url, text=text,
                                                 category="document"), doc_type=kind,
                                        meta={"pages": pages, "bytes": got["bytes"]})
        if doc_id is None:
            row = ctx.store.find_document_by_hash(Document(source_id="fetched", title=title[:300], url=url, text=text).content_hash)
            doc_id = row["id"] if row else None
    off = max(0, int(a.get("offset") or 0))
    n = max(500, min(int(a.get("max_chars") or 15000), 40000))
    out = {"doc_id": doc_id, "title": title, "url": url, "kind": kind, "pages": pages, "total_chars": len(text),
           "offset": off, "text": text[off:off + n], "more": off + n < len(text)}
    if not ctx.live:
        out["pit_warning"] = "fetched today: check its date is on or before the report date before relying on it"
    return out


# ============================================================================================ data sources
def t_fred_series(ctx: ToolContext, a: dict[str, Any]) -> Any:
    end = min(a.get("end") or ctx.asof, ctx.asof)
    out = market.fred_series(a["series_id"], a.get("start"), end)
    obs = out["observations"]
    if len(obs) > 120:
        out["observations"] = obs[-120:]
        out["note"] = f"showing the last 120 of {len(obs)} observations; narrow start/end for other ranges"
    if not ctx.live:
        out["pit_warning"] = "FRED returns today's vintage: past values may have been revised since the report date."
    return out


def t_worldbank(ctx: ToolContext, a: dict[str, Any]) -> Any:
    end_year = min(int(a.get("end_year") or date.fromisoformat(ctx.asof).year), date.fromisoformat(ctx.asof).year)
    return market.worldbank_indicator(a.get("country", "IN"), a["indicator"], a.get("start_year"), end_year)


# ============================================================================================ secondary
def t_news_search(ctx: ToolContext, a: dict[str, Any]) -> Any:
    days = int(a.get("days") or 7)
    since = (date.fromisoformat(ctx.asof) - timedelta(days=days)).isoformat()
    stored = memory.search_documents(ctx.store, a.get("query", ""), asof=ctx.asof, category="news", since=since,
                                     limit=_limit(a, 12, 40))
    out: dict[str, Any] = {"stored_news": stored,
                           "note": "News finds events; confirm facts in a primary source before relying on them."}
    if a.get("include_gdelt") and ctx.live:
        try:
            out["gdelt"] = market.gdelt_articles(a.get("query", ""), days=days, limit=_limit(a, 12, 40))
        except market.SourceError as exc:
            out["gdelt_error"] = str(exc)
    return out


def t_web_search(ctx: ToolContext, a: dict[str, Any]) -> Any:
    out = market.web_search(a["query"], limit=_limit(a, 8, 15))
    out["note"] = "Secondary source: confirm facts in a primary document (fetch_document) before citing."
    if not ctx.live:
        out["pit_warning"] = "web search is not point-in-time; ignore anything published after the report date."
    return out


# ============================================================================================ PTIS quant
def _bridge(ctx: ToolContext) -> PtisBridge:
    if ctx.bridge is None:
        ctx.bridge = PtisBridge()
    return ctx.bridge


def _bridge_call(fn: Callable[[], Any]) -> Any:
    try:
        return fn()
    except BridgeError as exc:
        raise ToolFailure(f"PTIS bridge: {exc}. Start it from the PTIS repo: "
                          "PTIS_ENV=test PYTHONPATH=. python -m research_bridge.server") from exc


def t_ptis_macro(ctx: ToolContext, a: dict[str, Any]) -> Any:
    return _bridge_call(lambda: _bridge(ctx).macro_state(ctx.asof))


def t_ptis_sectors(ctx: ToolContext, a: dict[str, Any]) -> Any:
    return _bridge_call(lambda: _bridge(ctx).sector_map(ctx.asof))


def t_ptis_sector_state(ctx: ToolContext, a: dict[str, Any]) -> Any:
    return _bridge_call(lambda: _bridge(ctx).sector_state(a["sector"], ctx.asof))


def t_ptis_sector_series(ctx: ToolContext, a: dict[str, Any]) -> Any:
    data = _bridge_call(lambda: _bridge(ctx).sector_series(a["sector"], ctx.asof, a.get("start") or "2020-01-01"))
    pts = data.get("series") or data.get("points") or []
    if isinstance(pts, list) and len(pts) > 260:
        data = {**data, "series": pts[-260:], "note": f"last 260 of {len(pts)} points"}
    return data


def t_ptis_event_study(ctx: ToolContext, a: dict[str, Any]) -> Any:
    events = [e for e in a.get("events", []) if e < ctx.asof]
    if not events:
        raise ToolFailure("give past event dates (YYYY-MM-DD) before the report date")
    return _bridge_call(lambda: _bridge(ctx).event_study(events, ctx.asof, sectors=a.get("sectors") or [],
                                                         syms=a.get("symbols") or [],
                                                         horizons=tuple(a.get("horizons") or (1, 5, 20, 60)),
                                                         condition=bool(a.get("condition_on_regime", True))))


def t_ptis_beneficiaries(ctx: ToolContext, a: dict[str, Any]) -> Any:
    events = [e for e in a.get("events", []) if e < ctx.asof]
    return _bridge_call(lambda: _bridge(ctx).beneficiaries(a["sector"], events, ctx.asof,
                                                           horizon=int(a.get("horizon") or 20), top=_limit(a, 8, 20)))


# ============================================================================================ calculators
def t_fno_cost(ctx: ToolContext, a: dict[str, Any]) -> Any:
    from ..tools.fno_costs import round_trip_cost
    charges = load_yaml("config/fno_charges.yaml")
    b = round_trip_cost(charges, trade_date=date.fromisoformat(a.get("date") or ctx.asof), instrument=a["instrument"],
                        buy_price=float(a["buy"]), sell_price=float(a["sell"]), quantity=int(a["qty"]))
    return b.as_dict()


# ============================================================================================ analyst panel
def personas() -> dict[str, dict[str, str]]:
    return yaml.safe_load((project_root() / "prompts" / "agent" / "personas.yaml").read_text(encoding="utf-8"))


def _prompt(name: str) -> str:
    return (project_root() / "prompts" / "agent" / f"{name}.md").read_text(encoding="utf-8")


def _evidence_block(ctx: ToolContext, refs: list[str] | None, max_chars: int = 40_000) -> str:
    chosen = [r for r in (refs or list(ctx.evidence)) if r in ctx.evidence]
    parts, used = [], 0
    for r in chosen:
        e = ctx.evidence[r]
        if e.get("tool") in ("consult_panel", "red_team"):
            continue
        body = json.dumps(e.get("result"), ensure_ascii=False, default=str)
        chunk = f"[{r}] {e['tool']}({json.dumps(e.get('args'), ensure_ascii=False)[:200]}):\n{body[:8000]}"
        if used + len(chunk) > max_chars:
            parts.append(f"... {len(chosen) - len(parts)} more evidence items omitted for length")
            break
        parts.append(chunk)
        used += len(chunk)
    return "\n\n".join(parts) or "(no evidence gathered yet)"


def _unsupported(ctx: ToolContext, out: dict[str, Any]) -> list[str]:
    allowed = allowed_from_evidence(ctx.evidence, [ctx.question])
    bad = []

    def walk(o: Any, key: str = "") -> None:
        if key in ("evidence_refs",):
            return
        if isinstance(o, str):
            bad.extend(t for t in numbers_in_text(o) if not _supported(t, allowed))
        elif isinstance(o, dict):
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)
    walk(out)
    return sorted(set(bad))


def t_consult_panel(ctx: ToolContext, a: dict[str, Any]) -> Any:
    seats = personas()
    wanted = [p for p in (a.get("personas") or list(seats)) if p in seats] or list(seats)
    evidence = _evidence_block(ctx, a.get("evidence_refs"))
    user = (f"Report date (asof): {ctx.asof}\nQuestion for the panel: {a['question']}\n\nEVIDENCE:\n{evidence}")

    def one(p: str) -> tuple[str, dict[str, Any], float]:
        system = _prompt("panel") + f"\n\n## Your seat: {seats[p]['name']}\n{seats[p]['focus']}"
        note, inr = ctx.ai.structured("research_panel", system, user, PanelNote)
        return p, note.model_dump(), inr

    with ThreadPoolExecutor(max_workers=int(ctx.cfg["agent"].get("parallel_tools", 4))) as ex:
        results = list(ex.map(one, wanted))
    notes, flags = {}, {}
    for p, note, inr in results:
        ctx.add_cost(inr)
        notes[p] = note
        bad = _unsupported(ctx, note)
        if bad:
            flags[p] = f"numbers not in the evidence (do not reuse them): {bad}"
    return {"notes": notes, "number_flags": flags}


def t_red_team(ctx: ToolContext, a: dict[str, Any]) -> Any:
    evidence = _evidence_block(ctx, a.get("evidence_refs"))
    user = f"Report date (asof): {ctx.asof}\nDRAFT CONCLUSION:\n{a['draft']}\n\nEVIDENCE:\n{evidence}"
    review, inr = ctx.ai.structured("research_panel", _prompt("red_team"), user, RedTeamReview)
    ctx.add_cost(inr)
    out = review.model_dump()
    bad = _unsupported(ctx, out)
    if bad:
        out["number_flags"] = f"numbers not in the evidence (do not reuse them): {bad}"
    return out


# ============================================================================================ playbooks
class _LegacyLLM:
    """Lets the milestone-1 budget-study pipeline run on whichever provider is configured."""

    def __init__(self, ai: Any, cfg: dict[str, Any]):
        self.ai = ai
        self.cfg = cfg["llm"]
        self.guard = ai.guard

    def structured(self, role: str, system: str, user: str, output_model: type) -> Any:
        model = self.ai.model_for("research_panel")
        max_tokens = int(self.cfg["max_tokens"].get(role, 8000))
        self.guard.check(model, len(system) + len(user), max_tokens, role=role)
        parsed, usage, used = self.ai.provider.structured(model, system, user, output_model, max_tokens, role)
        self.guard.record(role, used or model, usage)
        return parsed


def t_run_budget_study(ctx: ToolContext, a: dict[str, Any]) -> Any:
    from ..research.pipeline import run_research
    before = ctx.store.month_spend(date.today().strftime("%Y-%m"), "llm_research")
    res = run_research(a["topic"], ctx.asof, _LegacyLLM(ctx.ai, ctx.cfg), _bridge(ctx), store=ctx.store,
                       sectors=a.get("sectors") or None, out_dir=project_root() / "output" / "research", pdf=False)
    ctx.add_cost(ctx.store.month_spend(date.today().strftime("%Y-%m"), "llm_research") - before)
    pack = res["quant_pack"]
    return {"cio": res["cio"], "sectors_studied": res["sectors_studied"], "analogues": pack["analogues"],
            "sector_history": {s: {"history_abnormal_vs_nifty_pct": v.get("history_abnormal_vs_nifty_pct"),
                                   "beneficiaries_1m": v.get("beneficiaries_1m")} for s, v in pack["sectors"].items()},
            "caveats": pack["caveats"], "report_paths": res["paths"], "research_run_id": res.get("run_id")}


# ============================================================================================ registry
SUBMIT = "submit_research"


def registry() -> list[Tool]:
    kinds = {"type": "array", "items": {"type": "string", "enum": list(memory.KINDS)},
             "description": "record kinds to search (default all)"}
    return [
        Tool("memory_search", "Search the firm's research memory (events, expectations, reactions, market-structure "
             "changes, findings, notes) known by the report date. Start here: build on earlier work.",
             {"query": _s("words to search"), "kinds": kinds, "tags": _arr("mechanism tags that must all match"),
              "entities": _arr("symbols / sectors / institutions that must match"), "limit": _i("max records", 10)},
             ["query"], t_memory_search, "memory"),
        Tool("memory_similar", "Find past records that share mechanism tags (e.g. channel:rates, who-pays:consumers, "
             "stage:proposal) - events that WORK alike, not just sound alike.",
             {"tags": _arr("mechanism tags"), "kinds": kinds, "limit": _i("max records", 10)}, ["tags"],
             t_memory_similar, "memory"),
        Tool("documents_search", "Search documents already collected (regulator releases, filings, news, fetched "
             "documents), newest first, known by the report date.",
             {"query": _s("words to search"), "sources": _arr("source ids, e.g. rbi_press_releases, sebi_rss, "
                                                               "nse_announcements, fed_press_all, et_markets"),
              "category": _s("regulator | filing | news | document | calendar"), "symbol": _s("NSE symbol"),
              "since": _s("YYYY-MM-DD"), "limit": _i("max documents", 10)}, ["query"], t_documents_search, "memory"),
        Tool("read_stored_document", "Read the text of a stored document by id (from documents_search).",
             {"doc_id": _i("document id"), "offset": _i("character offset", 0), "max_chars": _i("characters", 12000)},
             ["doc_id"], t_read_stored_document, "memory"),
        Tool("regulator_feed", "Latest press releases / notifications from RBI, SEBI, PIB (Government of India) or "
             "the US Federal Reserve. Primary source.",
             {"source": _s("rbi | sebi | pib | fed", enum=sorted(FEEDS)), "days": _i("look-back days", 30),
              "query": _s("optional words to filter"), "limit": _i("max items", 15)}, ["source"], t_regulator_feed,
             "primary"),
        Tool("nse_announcements", "NSE corporate announcements (board meetings, results, orders, acquisitions, "
             "credit ratings...). Filter by symbol and dates. Primary source; attachments are PDFs for fetch_document.",
             {"symbol": _s("NSE symbol, e.g. TCS (optional)"), "from_date": _s("YYYY-MM-DD"), "to_date": _s("YYYY-MM-DD"),
              "query": _s("words that must appear in the subject/text"), "limit": _i("max rows", 15)}, [],
             t_nse_announcements, "primary"),
        Tool("nse_results", "A company's financial-result filings on NSE (newest first) with links to the XBRL data.",
             {"symbol": _s("NSE symbol"), "limit": _i("max filings", 8)}, ["symbol"], t_nse_results, "primary"),
        Tool("nse_result_figures", "Reported line items (revenue, expenses, profit, EPS; interest/NPA for banks) "
             "from a results XBRL link, per period, INR and crore.",
             {"xbrl_url": _s("the xbrl .xml link from nse_results")}, ["xbrl_url"], t_nse_result_figures, "primary"),
        Tool("nse_event_calendar", "Upcoming board meetings / results dates on NSE (all companies, or one symbol's "
             "history).", {"symbol": _s("NSE symbol (optional)"), "limit": _i("max rows", 20)}, [],
             t_nse_event_calendar, "primary"),
        Tool("nse_corporate_actions", "Dividends, splits, bonuses, buybacks with ex-dates.",
             {"symbol": _s("NSE symbol (optional)"), "limit": _i("max rows", 20)}, [], t_nse_corporate_actions,
             "primary"),
        Tool("nse_shareholding", "Quarterly shareholding pattern (promoter vs public %) for a company.",
             {"symbol": _s("NSE symbol"), "limit": _i("max quarters", 8)}, ["symbol"], t_nse_shareholding, "primary"),
        Tool("fetch_document", "Download an official document or web page by URL (PDF, HTML) and read its text in "
             "chunks. Use for filings' attachments, budget speeches, RBI/SEBI circulars, annual reports, Fed statements.",
             {"url": _s("http(s) URL"), "offset": _i("character offset", 0), "max_chars": _i("characters", 15000)},
             ["url"], t_fetch_document, "primary"),
        Tool("fred_series", "US/global macro series from FRED (e.g. FEDFUNDS, DGS10, CPIAUCSL, UNRATE, DEXINUS, "
             "DCOILBRENTEU).", {"series_id": _s("FRED series id"), "start": _s("YYYY-MM-DD"), "end": _s("YYYY-MM-DD")},
             ["series_id"], t_fred_series, "data", needs_key=("FRED_API_KEY",)),
        Tool("worldbank_indicator", "Annual World Bank indicators (e.g. FP.CPI.TOTL.ZG inflation, NY.GDP.MKTP.KD.ZG "
             "growth, BN.CAB.XOKA.GD.ZS current account % GDP).",
             {"indicator": _s("indicator code"), "country": _s("ISO code (default IN)"),
              "start_year": _i("first year"), "end_year": _i("last year")}, ["indicator"], t_worldbank, "data"),
        Tool("news_search", "Recent market news already collected (ET, Moneycontrol, Mint...), optionally plus "
             "GDELT global news. Secondary: use to find events, then confirm in primary sources.",
             {"query": _s("words to search"), "days": _i("look-back days", 7), "include_gdelt": {"type": "boolean"},
              "limit": _i("max items", 12)}, ["query"], t_news_search, "secondary"),
        Tool("web_search", "General web search (secondary). Use to find primary documents, expectations and "
             "consensus, then fetch_document the primary source.",
             {"query": _s("search query"), "limit": _i("max results", 8)}, ["query"], t_web_search, "secondary",
             needs_key=("TAVILY_API_KEY", "BRAVE_SEARCH_API_KEY", "SERPAPI_API_KEY")),
        Tool("ptis_macro_state", "India macro/market regime as of the report date from PTIS: VIX level and "
             "percentile, NIFTY vs 50/200DMA, midcap regime, USDINR, US10Y, DXY, crude.", {}, [], t_ptis_macro,
             "quant", needs_bridge=True),
        Tool("ptis_sector_map", "The NSE sectors PTIS can measure (exact names to use in other quant tools).", {}, [],
             t_ptis_sectors, "quant", needs_bridge=True),
        Tool("ptis_sector_state", "A sector now: 1/3/6/12-month returns, relative strength vs NIFTY, breadth, "
             "volatility, drawdown, growth medians.", {"sector": _s("exact sector name from ptis_sector_map")},
             ["sector"], t_ptis_sector_state, "quant", needs_bridge=True),
        Tool("ptis_sector_series", "Daily sector index series (equal-weight, point-in-time membership).",
             {"sector": _s("sector name"), "start": _s("YYYY-MM-DD")}, ["sector"], t_ptis_sector_series, "quant",
             needs_bridge=True),
        Tool("ptis_event_study", "Measured history: abnormal return vs NIFTY of sectors or stocks after past event "
             "dates, at 1/5/20/60 sessions, with n, median, IQR, hit rate, t, split by macro regime.",
             {"events": _arr("past event dates YYYY-MM-DD"), "sectors": _arr("sector names"),
              "symbols": _arr("NSE symbols"), "horizons": _arr("sessions", {"type": "integer"}),
              "condition_on_regime": {"type": "boolean"}}, ["events"], t_ptis_event_study, "quant", needs_bridge=True),
        Tool("ptis_beneficiaries", "A sector's liquid stocks ranked by their average abnormal return after past "
             "analogue events, with momentum and liquidity.",
             {"sector": _s("sector name"), "events": _arr("past event dates"), "horizon": _i("sessions", 20),
              "limit": _i("stocks", 8)}, ["sector", "events"], t_ptis_beneficiaries, "quant", needs_bridge=True),
        Tool("fno_cost", "True round-trip cost of an F&O trade under the rules in force on a date (STT, exchange, "
             "stamp, GST, brokerage).", {"instrument": _s("futures | options", enum=["futures", "options"]),
                                         "buy": {"type": "number"}, "sell": {"type": "number"},
                                         "qty": _i("quantity (units, not lots)"), "date": _s("YYYY-MM-DD")},
             ["instrument", "buy", "sell", "qty"], t_fno_cost, "tools"),
        Tool("consult_panel", "Ask the analyst panel (economist, sector_specialist, portfolio_manager, risk_manager, "
             "hedger, technical_trader, quant_manager) for their views on the evidence gathered so far. Paid.",
             {"question": _s("what you want their judgement on"),
              "personas": _arr("seats to consult (default all)"),
              "evidence_refs": _arr("evidence refs to show them (default all)")}, ["question"], t_consult_panel,
             "analysis", needs_ai=True),
        Tool("red_team", "Have a skeptic attack your draft conclusion before you submit. Paid.",
             {"draft": _s("your draft conclusion and main claims"), "evidence_refs": _arr("evidence refs")},
             ["draft"], t_red_team, "analysis", needs_ai=True),
        Tool("run_budget_study", "Playbook: the full Union Budget / policy sector study (scoper, cited facts, PTIS "
             "event-study pack over past budgets, 7-seat panel, skeptic, CIO). Expensive; use for budget questions.",
             {"topic": _s("e.g. Union Budget 2027"), "sectors": _arr("optional sector names")}, ["topic"],
             t_run_budget_study, "playbook", needs_bridge=True, needs_ai=True),
    ]


def submit_spec() -> ToolSpec:
    return ToolSpec(SUBMIT, "Submit the finished Research Object. This ends the research. Every number must come "
                            "from a tool result; cite evidence refs.", inline_refs(ResearchObject.model_json_schema()))


def available(ctx: ToolContext, bridge_ok: bool) -> tuple[list[Tool], list[dict[str, str]]]:
    tools, off = [], []
    for t in registry():
        if t.needs_key and not any(get_key(k) for k in t.needs_key):
            off.append({"tool": t.name, "why": f"needs {' or '.join(t.needs_key)} in .env"})
        elif t.needs_bridge and not bridge_ok:
            off.append({"tool": t.name, "why": "PTIS research bridge is not running"})
        else:
            tools.append(t)
    return tools, off


def execute(ctx: ToolContext, tool: Tool, args: dict[str, Any]) -> tuple[str, bool, Any]:
    """Run one tool; returns (ref, ok, result). Errors come back as a result with ok=False."""
    ref = ctx.next_ref()
    try:
        result = tool.handler(ctx, args or {})
        ok = True
    except (ToolFailure, market.SourceError, BridgeError, KeyError, ValueError) as exc:
        result, ok = {"error": f"{type(exc).__name__}: {exc}"}, False
    except Exception as exc:  # noqa: BLE001 - a broken tool must not kill the run
        result, ok = {"error": f"unexpected {type(exc).__name__}: {exc}"}, False
    if ok and isinstance(result, dict):
        lists = [v for v in result.values() if isinstance(v, list)]
        if lists and "count" not in result:
            result = {"count": len(lists[0]), **result}
    ctx.evidence[ref] = {"tool": tool.name, "args": args, "result": result, "ok": ok,
                         "at": datetime.now().isoformat(timespec="seconds")}
    return ref, ok, result
