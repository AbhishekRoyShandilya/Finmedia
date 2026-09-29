"""The Research Object (one verified result feeds every output) and the panel's structured outputs.

Strict models (extra fields forbidden) so the JSON schema sent to the model is complete and the object that is
stored is exactly what was checked.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Direction = Literal["positive", "negative", "neutral", "mixed"]
Confidence = Literal["low", "medium", "high"]
HorizonLabel = Literal["event day", "1 week", "1 month", "3 months", "longer"]
Mode = Literal["event_study", "company_deep_dive", "structure_forensics", "market_structure", "theme",
               "macro", "strategy_evidence", "other"]
Verdict = Literal["works", "does_not_work", "works_only_when", "not_applicable"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Section(_Strict):
    heading: str
    body: str = Field(description="Plain English. Numbers only as they appear in tool results.")
    evidence_refs: list[str] = Field(description="Refs like E3 of the tool results this section relies on")


class Claim(_Strict):
    target: str = Field(description="sector:<NSE sector name> | stock:<NSE symbol> | index:<name> | macro:<variable>")
    direction: Direction
    horizon: HorizonLabel
    confidence: Confidence
    rationale: str
    evidence_refs: list[str]


class SourceRef(_Strict):
    ref: str = Field(description="The evidence ref (E3) of the tool call that returned this source")
    title: str
    url: str = Field(description="URL as returned by the tool; empty if none")
    published_at: str = Field(description="As returned by the tool; empty if unknown")
    primary: bool = Field(description="True for filings, regulator/official documents and official data")


class PersonaView(_Strict):
    persona: str
    view: str


class EventMemory(_Strict):
    title: str
    event_date: str = Field(description="YYYY-MM-DD, or empty")
    event_type: str
    stage: Literal["proposal", "final", "effective", "happened", "scheduled", "unknown"]
    entities: list[str]
    mechanism_tags: list[str] = Field(description="e.g. who-pays:consumers, channel:rates, stage:proposal")
    summary: str
    evidence_refs: list[str]


class FindingMemory(_Strict):
    statement: str
    status: Literal["hypothesis", "supported", "killed"]
    evidence_refs: list[str]
    tags: list[str]
    review_after: str = Field(description="YYYY-MM-DD when this should be re-checked, or empty")


class StructureChangeMemory(_Strict):
    title: str
    effective_date: str = Field(description="YYYY-MM-DD, or empty")
    description: str
    affects: list[str] = Field(description="Strategies, participants or instruments affected")
    tags: list[str]
    evidence_refs: list[str]


class MemoryUpdates(_Strict):
    events: list[EventMemory]
    findings: list[FindingMemory]
    structure_changes: list[StructureChangeMemory]


class ResearchObject(_Strict):
    title: str
    question: str
    mode: Mode
    executive_summary: list[str] = Field(description="3-6 bullets a reader in a hurry can act on")
    verdict: Verdict
    verdict_conditions: str = Field(description="For works_only_when: the conditions; otherwise empty")
    sections: list[Section]
    claims: list[Claim]
    persona_views: list[PersonaView] = Field(description="One line per panel seat consulted; empty if none")
    risks: list[str]
    what_would_change_view: list[str]
    data_limits: list[str]
    sources: list[SourceRef]
    what_it_means_for_our_books: str = Field(description="INTERNAL ONLY. Effect on a momentum long book in Indian "
                                                         "small/mid caps, intraday trading and idle cash.")
    memory_updates: MemoryUpdates


# ------------------------------------------------------------------------------------------------ panel outputs
class PanelNote(_Strict):
    headline: str
    points: list[str]
    views: list[Claim]
    risks: list[str]
    missing_evidence: list[str]
    what_would_change_view: list[str]


class Challenge(_Strict):
    target: str
    challenge: str
    severity: Literal["minor", "material", "fatal"]
    evidence_refs: list[str]


class RedTeamReview(_Strict):
    challenges: list[Challenge]
    priced_in: list[str]
    alternative_explanations: list[str]
    missing_sources: list[str]
