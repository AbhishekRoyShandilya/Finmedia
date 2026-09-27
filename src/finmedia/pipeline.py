"""Pipeline steps: ingest -> prefilter -> triage -> brief -> Reel draft.

Each step is idempotent and safe to re-run. Paid (LLM) steps stop cleanly
when the monthly budget is reached.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .agents.brief import write_brief
from .agents.reel import write_reel
from .agents.triage import triage_document
from .config import load_yaml, path_setting, settings
from .costs import BudgetExceeded, BudgetGuard
from .lint import lint_reel
from .llm import LLM
from .models import Document
from .prefilter import score_document
from .review import render_review
from .sources import fetch_source
from .store import Store


def open_store() -> Store:
    return Store(path_setting("db_path"))


def make_llm(store: Store, client: Any | None = None) -> LLM:
    cfg = settings()
    return LLM(BudgetGuard(store, cfg), cfg, client=client)


# --------------------------------------------------------------- ingestion


def ingest(store: Store, only: str | None = None) -> dict[str, Any]:
    report: dict[str, Any] = {}
    inbox = path_setting("inbox_dir")
    for source in load_yaml("config/sources.yaml")["sources"]:
        if only and source["id"] != only:
            continue
        if not source.get("enabled", True) and source["id"] != only:
            continue
        try:
            docs = list(fetch_source(source, inbox_dir=inbox))
        except Exception as exc:  # network errors are reported, not fatal
            report[source["id"]] = {"error": str(exc)}
            continue
        added = sum(store.add_document(d) is not None for d in docs)
        report[source["id"]] = {"fetched": len(docs), "new": added}
    return report


def add_documents(store: Store, docs: list[Document]) -> int:
    return sum(store.add_document(d) is not None for d in docs)


def run_prefilter(store: Store) -> dict[str, int]:
    rules = load_yaml("config/prefilter.yaml")
    min_score = int(settings()["pipeline"]["prefilter_min_score"])
    kept = dropped = 0
    for row in list(store.documents(status="new")):
        doc = Document(source_id=row["source_id"], title=row["title"], url=row["url"] or "",
                       text=row["text"] or "")
        result = score_document(doc, rules, min_score)
        store.set_prefilter(row["id"], result.score, result.reasons, result.keep)
        kept += result.keep
        dropped += not result.keep
    return {"kept": kept, "dropped": dropped}


# ------------------------------------------------------------- LLM steps


def run_triage(store: Store, llm: LLM, limit: int | None = None) -> dict[str, Any]:
    cfg = settings()
    limit = limit or int(cfg["pipeline"]["triage_limit_per_run"])
    done, stopped = [], None
    for row in list(store.documents(status="kept", limit=limit)):
        try:
            result = triage_document(llm, row, cfg)
        except BudgetExceeded as exc:
            stopped = str(exc)
            break
        store.save_triage(row["id"], result.model_dump(mode="json"))
        done.append({"id": row["id"], "title": row["title"], "materiality": result.materiality,
                     "playbook": result.playbook_id})
    return {"triaged": done, "stopped": stopped}


def run_brief(store: Store, llm: LLM, doc_id: int) -> dict[str, Any]:
    row = store.get_document(doc_id)
    triage = store.get_triage(doc_id)
    if row is None or triage is None:
        raise ValueError(f"Document {doc_id} not found or not triaged yet")
    brief, verification = write_brief(llm, row, triage, settings())
    store.save_brief(doc_id, brief.model_dump(mode="json"), verification)
    return {"brief": brief.model_dump(mode="json"), "verification": verification}


def run_reel(store: Store, llm: LLM, doc_id: int, series: str = "event", notes: str = "") -> dict[str, Path]:
    brief = store.get_brief(doc_id)
    if brief is None:
        raise ValueError(f"No brief for document {doc_id}; run `finmedia brief {doc_id}` first")
    plan = write_reel(llm, brief, series=series, notes=notes).model_dump(mode="json")
    lint = lint_reel(plan, load_yaml("config/lint_rules.yaml"), brief=brief)
    return save_reel_outputs(doc_id, plan, lint.as_dict(), brief)


def save_reel_outputs(doc_id: int, plan: dict[str, Any], lint: dict[str, Any],
                      brief: dict[str, Any]) -> dict[str, Path]:
    out = path_setting("output_dir") / "reels"
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{datetime.now():%Y%m%d-%H%M}-doc{doc_id}"
    plan_path = out / f"{stem}.plan.json"
    review_path = out / f"{stem}.review.md"
    plan_path.write_text(json.dumps({"plan": plan, "lint": lint}, ensure_ascii=False, indent=2), encoding="utf-8")
    review_path.write_text(render_review(plan, lint, brief), encoding="utf-8")
    return {"plan": plan_path, "review": review_path}


def run_daily(store: Store, llm: LLM, reels: int = 1) -> dict[str, Any]:
    """Ingest everything, triage, and draft Reels for the most material items."""
    report: dict[str, Any] = {"ingest": ingest(store), "prefilter": run_prefilter(store)}
    report["triage"] = run_triage(store, llm)
    min_mat = int(settings()["pipeline"]["brief_min_materiality"])
    drafts = []
    for row in store.top_triaged(min_mat, reels):
        try:
            run_brief(store, llm, row["id"])
            paths = run_reel(store, llm, row["id"])
        except BudgetExceeded as exc:
            report["stopped"] = str(exc)
            break
        drafts.append({k: str(v) for k, v in paths.items()})
    report["reel_drafts"] = drafts
    return report
