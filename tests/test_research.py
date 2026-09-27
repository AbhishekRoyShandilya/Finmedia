"""Deep Research Desk: verifier, budget pool, case library, end-to-end pipeline with a fake LLM and a fake bridge."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from finmedia.costs import BudgetGuard, Usage, month_key
from finmedia.llm import LLM
from finmedia.research.cases import analogue_dates
from finmedia.research.models import (Beneficiary, CioSynthesis, CitedFact, FactSheet, PersonaView, ResearchScope,
                                      SectorVerdict, SectorView, SkepticReview)
from finmedia.research.pipeline import run_research, score_claims
from finmedia.research.render import public_lint
from finmedia.research.verify import allowed_values, check_numbers

DOC = "The allocation for capital expenditure is 11.21 lakh crore. Customs duty on solar glass is removed."


class FakeBridge:
    def __init__(self):
        self.calls = []

    def sector_map(self, asof):
        return {"sectors": ["Capital Goods", "Power", "Automobile and Auto Components"]}

    def macro_state(self, asof):
        return {"india_vix": 14.2, "vix_pct_rank_1y": 31.5, "nifty_vs_200dma_pct": 4.4}

    def sector_state(self, sector, asof):
        return {"asof": asof, "sector": sector, "kind": "official NSE index", "ret_1m_pct": 2.46, "rs_3m_pct": -1.12}

    def event_study(self, events, asof, sectors=None, horizons=(1, 5, 20, 60), condition=True, syms=None):
        self.calls.append(dict(events=events, asof=asof, sectors=sectors, syms=syms, horizons=horizons))
        summ = {str(h): {"n": 19, "mean": -1.71, "median": -3.03, "q25": -5.14, "q75": -0.41, "hit_rate_pct": 26.32,
                         "t": -2.35, "min": -9.8, "max": 4.1,
                         "vix_high=False": {"n": 11, "median": -2.2, "q25": -4.0, "q75": 0.3, "hit_rate_pct": 36.36}}
                for h in horizons}
        per = [{"event": e, "h": 20, "abn": -1.0} for e in events if e >= "2008"]
        tg = {f"sector:{s}": {"kind": "official NSE index", "summary": summ, "per_event": per} for s in sectors or []}
        tg.update({f"stock:{s}": {"kind": "stock", "summary": summ, "per_event": per} for s in syms or []})
        return {"targets": tg}

    def beneficiaries(self, sector, events, asof, horizon=20, top=5):
        return {"ranked": [{"sym": "KAYNES", "events_n": 3, "avg_abn_pct": 6.54, "median_abn_pct": 5.02,
                            "hit_rate_pct": 66.67, "mom_6m_pct": 18.9, "liquidity_rank": 140}],
                "method": "avg abnormal return"}


def _view(persona, text):
    return PersonaView(persona=persona, headline="Capex tilt", key_points=[text],
                       sector_views=[SectorView(sector="Capital Goods", direction="negative", horizon="1 month",
                                                confidence="medium", rationale=text, evidence=["history"])],
                       risks=["execution"], instruments_or_actions=["underweight"], what_would_change_view=["orders"])


def _cio(sym="KAYNES"):
    return CioSynthesis(
        title="Budget study", summary="Capital Goods lagged NIFTY after past budgets, median -3.03 over 1 month.",
        sector_verdicts=[SectorVerdict(sector="Capital Goods", direction="negative", horizon="1 month",
                                       confidence="medium", expected_range="median -3.03, middle half -5.14 to -0.41, n 19",
                                       rationale="hit rate 26.32 with t -2.35", what_would_change_view=["orders"],
                                       top_beneficiaries=[Beneficiary(sym=sym, why="avg 6.54 over 3 events")],
                                       dates_to_watch=["results season"])],
        disagreements=["none"], caveats=["small n"])


class DeskFake:
    """client.beta.messages.parse stand-in. The economist's first answer contains a fabricated number (7.77)."""

    def __init__(self, cio_sym="KAYNES", economist_always_bad=False):
        self.calls, self.cio_sym, self.always_bad = [], cio_sym, economist_always_bad

    def parse(self, **kw):
        self.calls.append(kw)
        user, fmt = kw["messages"][0]["content"], kw["output_format"]
        if fmt is ResearchScope:
            out = ResearchScope(topic="Union Budget 2025", playbook_id="fiscal_structural_policy", event_type="fiscal.budget",
                                analogue_set="full_budgets", sectors=["Capital Goods", "Made Up Sector"],
                                variables=["yields"], research_questions=["q"], why_these_sectors="capex")
        elif fmt is FactSheet:
            out = FactSheet(status_note="speech", facts=[
                CitedFact(claim="Capex is 11.21 lakh crore",
                          source_quote="The allocation for capital expenditure is 11.21 lakh crore.", sectors=["Capital Goods"]),
                CitedFact(claim="Invented", source_quote="This sentence is not in the document.", sectors=["Power"])])
        elif fmt is PersonaView:
            bad = "You are the economist" in user and (self.always_bad or "REJECTED" not in user)
            out = _view("x", "sector fell 7.77 after budgets" if bad else "median -3.03 on n 19 since 2005")
        elif fmt is SkepticReview:
            out = SkepticReview(challenges=[], priced_in_notes=["1 month return 2.46"], data_limits=["n 19"])
        else:
            out = _cio(self.cio_sym)
        return SimpleNamespace(parsed_output=out, stop_reason="end_turn", stop_details=None, model=kw["model"],
                               usage=SimpleNamespace(input_tokens=2000, output_tokens=800,
                                                     cache_creation_input_tokens=0, cache_read_input_tokens=0))


def _llm(store, cfg, fake):
    return LLM(BudgetGuard(store, cfg), cfg, client=SimpleNamespace(beta=SimpleNamespace(messages=fake)))


# ------------------------------------------------------------------ verifier

def test_verifier_catches_planted_number_and_allows_pack_values():
    pack = {"a": {"median": -3.03, "n": 19, "t": -2.35}}
    allowed = allowed_values(pack, [{"claim": "Capex is 11.21 lakh crore", "source_quote": "11.21 lakh crore"}])
    ok = check_numbers({"r": "Lagged by 3.03 (n 19, t -2.35) after Budget 2024 on 23 July 2024; capex 11.21"}, allowed)
    assert ok["ok"], ok
    bad = check_numbers({"r": "It will fall 7.77 percent", "evidence": ["99.9 ignored here"]}, allowed)
    assert bad["unsupported"] == ["7.77"]
    assert check_numbers({"r": "about 3.0"}, allowed)["ok"]           # coarser rounding of -3.03 is fine
    assert not check_numbers({"r": "median 3.1"}, allowed)["ok"]      # a different value at that precision is not


def test_analogues_strictly_before_asof():
    d = analogue_dates("full_budgets", "2025-02-01")
    assert "2025-02-01" not in d and "2024-07-23" in d and "2024-02-01" not in d   # interim excluded
    assert all(x < "2025-02-01" for x in d)


def test_research_spend_uses_separate_pool(store, cfg):
    g = BudgetGuard(store, cfg)
    media_before = g.remaining_llm_inr()
    g.record("research_cio", "claude-opus-5", Usage(input_tokens=100_000, output_tokens=10_000))
    assert store.month_spend(month_key(), "llm_research") > 0
    assert g.remaining_llm_inr() == pytest.approx(media_before)
    assert g.remaining_llm_inr(pool="llm_research") < float(cfg["budget"]["research_llm_cap_inr"])


# ------------------------------------------------------------------ pipeline

def test_pipeline_end_to_end(store, cfg, tmp_path):
    doc = tmp_path / "speech.txt"
    doc.write_text(DOC, encoding="utf-8")
    fake, bridge = DeskFake(), FakeBridge()
    res = run_research("Union Budget 2025", "2025-02-01", _llm(store, cfg, fake), bridge, store=store,
                       docs=[str(doc)], out_dir=tmp_path / "out", pdf=False)
    assert res["sectors_studied"] == ["Capital Goods"] and res["scoper_rejected_sectors"] == ["Made Up Sector"]
    assert len(res["facts"]) == 1 and len(res["facts_dropped_bad_quote"]) == 1
    assert res["verification"]["persona:economist"]["attempts"] == 2
    assert not any(v.get("flagged") for v in res["verification"].values()), res["verification"]
    assert set(res["personas"]) >= {"economist", "hedger", "quant_manager"}
    an = res["quant_pack"]["analogues"]
    assert all("2025-02-01" > e for e in an["events"])
    assert an["n_events"] == len(an["events"]) < an["n_listed"] and an["not_measured"][0] == "1997-02-28"
    assert any("not measured" in c for c in res["quant_pack"]["caveats"])
    assert store.month_spend(month_key(), "llm") == 0 and store.month_spend(month_key(), "llm_research") > 0
    # public edition: no stock names, no direction language
    public = open(res["paths"]["public"], encoding="utf-8").read()
    assert res["paths"]["public_lint_hits"] == [] and "KAYNES" not in public
    internal = open(res["paths"]["internal"], encoding="utf-8").read()
    assert "KAYNES" in internal and "INTERNAL" in internal
    rows = store.claims()
    assert {r["target"] for r in rows} >= {"sector:Capital Goods", "stock:KAYNES"}


def test_persistent_fabrication_is_flagged(store, cfg, tmp_path):
    res = run_research("Union Budget 2025", "2025-02-01", _llm(store, cfg, DeskFake(economist_always_bad=True)),
                       FakeBridge(), out_dir=tmp_path, render=False)
    v = res["verification"]["persona:economist"]
    assert v["flagged"] and v["unsupported"] == ["7.77"]


def test_cio_stock_outside_table_is_flagged(store, cfg, tmp_path):
    res = run_research("Union Budget 2025", "2025-02-01", _llm(store, cfg, DeskFake(cio_sym="RELIANCE")),
                       FakeBridge(), out_dir=tmp_path, render=False)
    assert res["verification"]["cio"]["flagged"]
    assert res["verification"]["cio"]["beneficiaries_not_in_table"] == ["Capital Goods:RELIANCE"]


def test_public_lint_catches_direction_and_stock():
    result = {"quant_pack": {"sectors": {"X": {"beneficiaries_1m": [{"sym": "KAYNES"}]}}},
              "cio": {"sector_verdicts": []}}
    hits = public_lint("<p>We are overweight KAYNES</p>", result, rules={"recommendation_phrases": []})
    assert "phrase:overweight" in hits and "stock:KAYNES" in hits


def test_postmortem_scores_from_report_date_close(store):
    run = store.save_research_run("t", "2025-01-31", {}, None, None)
    store.add_claims(run, "2025-01-31", [dict(target="sector:Capital Goods", direction="negative", horizon="1 month",
                                              confidence="medium", source="cio")])
    bridge = FakeBridge()
    out = score_claims(store, bridge, "2025-03-31")
    assert out["scored"] == 1
    assert bridge.calls[0]["events"] == ["2025-02-01"] and bridge.calls[0]["horizons"] == (20,)
    import json
    oc = json.loads(store.claims()[0]["outcome_json"])
    assert oc["hit"] is True and oc["abnormal_pct"] == -3.03


def test_vocabulary_numbers_are_not_claims():
    allowed = allowed_values({"a": {"median": -3.03}})
    txt = {"r": "Over 3 months and 1 week, vs its 200DMA, 52-week high, NIFTY 50 and Midcap 100: 3.03"}
    assert check_numbers(txt, allowed)["ok"]
    assert not check_numbers({"r": "fell 4.4 in 3 months"}, allowed)["ok"]
