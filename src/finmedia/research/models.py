"""Structured outputs for the Deep Research Desk. Strict (extra fields forbidden, every field required) so the JSON
schema sent to the API is complete - the same convention as finmedia.models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

Direction = Literal["positive", "negative", "neutral", "mixed"]
Confidence = Literal["low", "medium", "high"]
HorizonLabel = Literal["event day", "1 week", "1 month", "3 months", "longer"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ------------------------------------------------------------------ 1. scoper
class ResearchScope(_Strict):
    topic: str
    playbook_id: str                    # from system/event_playbooks.yaml
    event_type: str
    analogue_set: Literal["full_budgets", "interim_budgets", "all_budgets", "none"]
    sectors: list[str]                  # EXACT names from the allowed sector list given in the prompt
    variables: list[str]                # macro variables that transmit the event (rates, crude, rupee ...)
    research_questions: list[str]
    why_these_sectors: str


# ------------------------------------------------------------------ 2. facts (cited)
class CitedFact(_Strict):
    claim: str
    source_quote: str                   # exact words from a provided document
    sectors: list[str]


class FactSheet(_Strict):
    facts: list[CitedFact]
    status_note: str


# ------------------------------------------------------------------ 4. personas
class SectorView(_Strict):
    sector: str
    direction: Direction
    horizon: HorizonLabel
    confidence: Confidence
    rationale: str                      # numbers ONLY from the quant pack or the cited facts
    evidence: list[str]                 # quant-pack keys or fact claims relied on


class PersonaView(_Strict):
    persona: str
    headline: str
    key_points: list[str]
    sector_views: list[SectorView]
    risks: list[str]
    instruments_or_actions: list[str]   # hedges (Hedger), allocations (PM), levels / triggers (Technical) ...
    what_would_change_view: list[str]


# ------------------------------------------------------------------ 5. skeptic + CIO
class Challenge(_Strict):
    target: str                         # persona or sector challenged
    challenge: str
    severity: Literal["minor", "material", "fatal"]


class SkepticReview(_Strict):
    challenges: list[Challenge]
    priced_in_notes: list[str]
    data_limits: list[str]


class Beneficiary(_Strict):
    sym: str
    why: str                            # must cite the beneficiaries table numbers


class SectorVerdict(_Strict):
    sector: str
    direction: Direction
    horizon: HorizonLabel
    confidence: Confidence
    expected_range: str                 # from the event-study IQR / median in the quant pack, stated with n
    rationale: str
    top_beneficiaries: list[Beneficiary]
    what_would_change_view: list[str]
    dates_to_watch: list[str]


class CioSynthesis(_Strict):
    title: str
    summary: str
    sector_verdicts: list[SectorVerdict]
    disagreements: list[str]            # where personas disagreed and how it was resolved
    caveats: list[str]
