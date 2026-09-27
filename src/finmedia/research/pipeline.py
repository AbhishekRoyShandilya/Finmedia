"""Deep Research Desk - fixed-order workflow:

  1 Scoper -> 2 Fact Extractor (quotes verified) -> 3 Quant pack (PTIS bridge, deterministic)
  -> 4 Persona panel (parallel) -> 5 Skeptic -> CIO, each output number-verified (regenerate once, then flag)
  -> 6 Render (internal + public edition) -> 7 Store run + claims ledger.

The LLM never supplies a number: every figure must match the quant pack or a verified quote.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from ..agents.prompts import system_prompt
from ..costs import BudgetExceeded, BudgetGuard
from ..llm import LLM
from ..sources.inbox import _read_pdf
from ..store import Store
from ..tools.ptis import PtisBridge
from .models import CioSynthesis, FactSheet, PersonaView, ResearchScope, SkepticReview
from .quant import build_pack
from .verify import allowed_values, check_numbers, quotes_present

T = TypeVar("T", bound=BaseModel)

PERSONAS = ["economist", "sector_specialist", "portfolio_manager", "risk_manager", "hedger",
            "technical_trader", "quant_manager"]
PACK_CHARS_GUESS = 40_000       # a 6-8 sector quant pack serialises to roughly this


def _system(role_file: str) -> str:
    return system_prompt("research_rules") + "\n\n" + system_prompt(role_file)


def _j(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1, default=str)


def read_docs(paths: list[str], max_chars: int) -> str:
    parts = []
    for p in map(Path, paths):
        text = _read_pdf(p) if p.suffix.lower() == ".pdf" else p.read_text(encoding="utf-8", errors="replace")
        parts.append(f"=== DOCUMENT: {p.name} ===\n{text}")
    return "\n\n".join(parts)[:max_chars]


def estimate_inr(guard: BudgetGuard, cfg: dict[str, Any], doc_chars: int = 0) -> dict[str, float]:
    """Worst case of one report (every call at max_tokens, verification retries excluded)."""
    llm = cfg["llm"]

    def call(role: str, chars: int) -> float:
        return guard.worst_case_inr(llm["models"][role], chars, int(llm["max_tokens"][role]))

    est = {"scoper": call("research_scoper", 8_000),
           "facts": call("research_facts", min(doc_chars, int(llm["max_doc_chars"]["research_facts"]))) if doc_chars else 0.0,
           "personas": len(PERSONAS) * call("research_persona", PACK_CHARS_GUESS + 12_000),
           "skeptic": call("research_skeptic", PACK_CHARS_GUESS + 60_000),
           "cio": call("research_cio", PACK_CHARS_GUESS + 70_000)}
    est["total"] = sum(est.values())
    est["research_budget_left"] = guard.remaining_llm_inr(pool="llm_research")
    return est


def _verified(llm: LLM, role: str, system: str, user: str, model: type[T],
              allowed: list[float]) -> tuple[T, dict[str, Any]]:
    out = llm.structured(role, system, user, model)
    chk = check_numbers(out.model_dump(), allowed)
    attempts = 1
    if not chk["ok"]:
        retry = (user + "\n\nYOUR PREVIOUS ANSWER WAS REJECTED. These numbers are not in the quant pack or the cited "
                 f"facts: {chk['unsupported']}. Rewrite it using only numbers exactly as provided, or words.")
        out = llm.structured(role, system, retry, model)
        chk = check_numbers(out.model_dump(), allowed)
        attempts = 2
    return out, {**chk, "attempts": attempts, "flagged": not chk["ok"]}


def _beneficiary_check(cio: CioSynthesis, pack: dict[str, Any]) -> list[str]:
    bad = []
    for v in cio.sector_verdicts:
        table = {r.get("sym") for r in pack["sectors"].get(v.sector, {}).get("beneficiaries_1m", [])}
        bad += [f"{v.sector}:{b.sym}" for b in v.top_beneficiaries if b.sym not in table]
    return bad


def run_research(topic: str, asof: str, llm: LLM, bridge: PtisBridge, store: Store | None = None,
                 docs: list[str] | None = None, sectors: list[str] | None = None,
                 out_dir: str | Path = "output/research", render: bool = True, pdf: bool = True) -> dict[str, Any]:
    cfg = llm.cfg
    doc_text = read_docs(docs or [], int(cfg["max_doc_chars"]["research_facts"]))
    est = estimate_inr(llm.guard, {"llm": cfg}, len(doc_text))
    if est["total"] > est["research_budget_left"]:
        raise BudgetExceeded(f"Report worst case ₹{est['total']:.0f} exceeds the research budget left "
                             f"₹{est['research_budget_left']:.0f}.")

    allowed_sectors = bridge.sector_map(asof)["sectors"]
    header = f"asof (report date): {asof}\ntopic: {topic}\n"

    # 1 scope
    scope = llm.structured("research_scoper", _system("research_scoper"),
                           header + "allowed sectors: " + _j(allowed_sectors), ResearchScope)
    rejected = [s for s in scope.sectors if s not in allowed_sectors]
    chosen = [s for s in (sectors or scope.sectors) if s in allowed_sectors]
    if not chosen:
        raise ValueError(f"No valid sectors (scoper proposed {scope.sectors}; allowed {allowed_sectors}).")

    # 2 facts (quotes must be verbatim in the documents)
    facts: list[dict[str, Any]] = []
    fact_note, dropped_facts = "no primary documents provided", []
    if doc_text:
        sheet = llm.structured("research_facts", _system("research_facts"),
                               header + "allowed sectors: " + _j(allowed_sectors) + "\n\n" + doc_text, FactSheet)
        all_facts = [f.model_dump() for f in sheet.facts]
        missing = set(quotes_present(all_facts, doc_text))
        facts = [f for f in all_facts if f["source_quote"] not in missing]
        dropped_facts = [f for f in all_facts if f["source_quote"] in missing]
        fact_note = sheet.status_note

    # 3 quant
    pack = build_pack(bridge, chosen, scope.analogue_set, asof)
    allowed = allowed_values(pack, facts)
    context = (header + "\nRESEARCH SCOPE:\n" + _j(scope.model_dump()) + "\n\nCITED FACTS:\n" + _j(facts)
               + "\n\nQUANT PACK:\n" + _j(pack))

    # 4 persona panel (parallel)
    def persona(name: str) -> tuple[str, PersonaView, dict[str, Any]]:
        view, chk = _verified(llm, "research_persona", _system(f"personas/{name}"),
                              context + f"\n\nYou are the {name.replace('_', ' ')}. Cover every studied sector.",
                              PersonaView, allowed)
        view = view.model_copy(update={"persona": name})
        return name, view, chk

    with ThreadPoolExecutor(max_workers=4) as ex:
        panel = list(ex.map(persona, PERSONAS))
    views = {n: v.model_dump() for n, v, _ in panel}
    verification = {f"persona:{n}": c for n, _, c in panel}

    # 5 skeptic -> CIO
    skeptic, verification["skeptic"] = _verified(
        llm, "research_skeptic", _system("research_skeptic"), context + "\n\nPERSONA PANEL:\n" + _j(views),
        SkepticReview, allowed)
    cio, verification["cio"] = _verified(
        llm, "research_cio", _system("research_cio"),
        context + "\n\nPERSONA PANEL:\n" + _j(views) + "\n\nSKEPTIC REVIEW:\n" + _j(skeptic.model_dump()),
        CioSynthesis, allowed)
    verification["cio"]["beneficiaries_not_in_table"] = _beneficiary_check(cio, pack)
    if verification["cio"]["beneficiaries_not_in_table"]:
        verification["cio"]["flagged"] = True

    result: dict[str, Any] = {
        "topic": topic, "asof": asof, "scope": scope.model_dump(), "sectors_studied": chosen,
        "scoper_rejected_sectors": rejected, "facts": facts, "facts_dropped_bad_quote": dropped_facts,
        "fact_status_note": fact_note, "quant_pack": pack, "personas": views, "skeptic": skeptic.model_dump(),
        "cio": cio.model_dump(), "verification": verification, "cost_estimate_inr": est,
    }

    paths: dict[str, str | None] = {"internal": None, "public": None}
    if render:
        from .render import render_all
        paths = render_all(result, Path(out_dir), pdf=pdf)
    result["paths"] = paths

    if store is not None:
        run_id = store.save_research_run(topic, asof, result, paths.get("internal"), paths.get("public"))
        store.add_claims(run_id, asof, claims_from(result))
        result["run_id"] = run_id
    return result


def claims_from(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for v in result["cio"]["sector_verdicts"]:
        rows.append(dict(target=f"sector:{v['sector']}", direction=v["direction"], horizon=v["horizon"],
                         confidence=v["confidence"], source="cio"))
        for b in v["top_beneficiaries"]:
            rows.append(dict(target=f"stock:{b['sym']}", direction=v["direction"], horizon=v["horizon"],
                             confidence=v["confidence"], source="cio"))
    for name, view in result["personas"].items():
        for sv in view["sector_views"]:
            rows.append(dict(target=f"sector:{sv['sector']}", direction=sv["direction"], horizon=sv["horizon"],
                             confidence=sv["confidence"], source=f"persona:{name}"))
    return rows


# ------------------------------------------------------------------ postmortem

HORIZON_SESSIONS = {"event day": 1, "1 week": 5, "1 month": 20, "3 months": 60, "longer": 60}


def score_claims(store: Store, bridge: PtisBridge, today: str) -> dict[str, Any]:
    """Score unscored claims whose horizon has passed: the realised abnormal return vs NIFTY measured from the last
    close ON OR BEFORE the report date (the bridge bases a path on the close before the first session on/after the
    event, so the event passed is asof + 1 day - a claim written on budget eve gets no credit for that day)."""
    scored, pending, failed = 0, 0, []
    for c in store.claims(unscored_only=True):
        h = HORIZON_SESSIONS[c["horizon"]]
        kind, name = c["target"].split(":", 1)
        try:
            start = (date.fromisoformat(c["asof"]) + timedelta(days=1)).isoformat()
            es = bridge.event_study([start], today, sectors=[name] if kind == "sector" else [],
                                    syms=[name] if kind == "stock" else [], horizons=(h,), condition=False)
        except Exception as exc:          # noqa: BLE001 - report and continue
            failed.append(f"{c['id']}: {exc}")
            continue
        summ = es["targets"].get(c["target"], {}).get("summary", {}).get(str(h), {})
        if not summ.get("n"):
            pending += 1                  # horizon not complete yet
            continue
        realised = summ["median"]
        want = {"positive": 1, "negative": -1}.get(c["direction"])
        store.set_claim_outcome(c["id"], {"scored_on": today, "horizon_sessions": h, "abnormal_pct": realised,
                                          "hit": None if want is None else (realised * want > 0)})
        scored += 1
    return {"scored": scored, "pending": pending, "failed": failed}
