from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from finmedia.config import load_yaml, settings
from finmedia.costs import BudgetGuard
from finmedia.llm import LLM
from finmedia.models import (Exposure, Fact, ReelPlan, ResearchBrief, Scene, TriageResult,
                             VisualType)
from finmedia.store import Store

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "test.db")
    yield s
    s.close()


@pytest.fixture
def cfg():
    return settings()


@pytest.fixture
def lint_rules():
    return load_yaml("config/lint_rules.yaml")


def sample_triage() -> TriageResult:
    return TriageResult(
        is_market_relevant=True, playbook_id="market_structure_flows",
        event_type="regulatory.proposal.expiry_rules", materiality=78, horizon="H1",
        status="proposal", primary_entities=["index options traders"],
        summary="A consultation paper proposes reviewing expiry-day rules.",
        why_it_matters="Changes expiry-day costs for option sellers.", needs_human_now=True,
    )


def sample_brief() -> ResearchBrief:
    return ResearchBrief(
        headline="Regulator proposes review of expiry-day derivatives rules",
        status_note="Consultation paper; comments by 15 October 2026",
        facts=[Fact(claim="59% of index options turnover is in same-day-expiry contracts",
                    source_quote="59% of index options turnover occurs in same-day-expiry contracts")],
        mechanism="Higher expiry-day margin raises the cost of short options on expiry day.",
        exposures=[Exposure(entity="Retail option sellers", order="first", direction="negative",
                            size="medium", rationale="More margin blocked on expiry day")],
        participants=["Retail traders face higher capital needs on expiry day"],
        history_questions=["Option turnover T+1 to T+60 after the Nov 2024 measures"],
        skeptic_points=["It is only a proposal"],
        what_would_change_view=["Final rule drops the margin proposal"],
        daily_life_anchor="A friend's expiry-day options screenshot",
        compliance_tier="E",
    )


def sample_reel() -> ReelPlan:
    return ReelPlan(
        series="Event Explainer",
        hook_text="59% trading सिर्फ़ expiry वाले दिन?",
        scenes=[
            Scene(id="s1", visual=VisualType.AVATAR,
                  narration="आपके किसी दोस्त ने expiry वाले दिन का screenshot ज़रूर भेजा होगा। [beat]",
                  on_screen_text="Expiry day", visual_spec="desk look"),
            Scene(id="s2", visual=VisualType.CHART,
                  narration="Index options का 59 percent कारोबार उसी दिन की expiry वाले contracts में होता है।",
                  on_screen_text="59%", visual_spec="bar: same-day expiry share"),
            Scene(id="s3", visual=VisualType.DOC_RECEIPT,
                  narration="अब regulator ने expiry day के rules की समीक्षा का proposal रखा है। ये अभी final नहीं है।",
                  on_screen_text="Consultation paper", visual_spec="highlight section 2"),
            Scene(id="s4", visual=VisualType.AVATAR,
                  narration="Final rule आने तक हम इस पर नज़र रखेंगे। पूरा हिसाब हमारे WhatsApp channel पर है।",
                  on_screen_text="Proposal ≠ final", visual_spec="standing look"),
        ],
        caption="Expiry day ka asli hisaab. Source: consultation paper.",
        hashtags=["#FnO", "#SEBI", "#Nifty", "#StockMarketIndia", "#Finmedia"],
        title_variants=["Expiry Day Ka Asli Hisaab", "Expiry day का असली हिसाब", "The Real Math of Expiry Day"],
        disclosure="This video uses an AI-generated voice and avatar of the founder. Not investment advice.",
        sources=["Consultation paper (synthetic test fixture)"],
        compliance_tier="E",
    )


class FakeMessages:
    """Mimics client.beta.messages.parse, returning canned outputs by type."""

    def __init__(self, stop_reason: str = "end_turn"):
        self.calls: list[dict] = []
        self.stop_reason = stop_reason

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        fmt = kwargs["output_format"]
        parsed = {TriageResult: sample_triage, ResearchBrief: sample_brief, ReelPlan: sample_reel}[fmt]()
        return SimpleNamespace(
            parsed_output=None if self.stop_reason == "refusal" else parsed,
            stop_reason=self.stop_reason,
            stop_details=SimpleNamespace(category="test", explanation="test"),
            model=kwargs["model"],
            usage=SimpleNamespace(input_tokens=1000, output_tokens=500,
                                  cache_creation_input_tokens=0, cache_read_input_tokens=0),
        )


@pytest.fixture
def fake_client():
    messages = FakeMessages()
    return SimpleNamespace(beta=SimpleNamespace(messages=messages))


@pytest.fixture
def llm(store, cfg, fake_client):
    return LLM(BudgetGuard(store, cfg), cfg, client=fake_client)
