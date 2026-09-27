"""Data models shared across the pipeline.

The models used as LLM structured outputs forbid extra fields and make every
field required, so the JSON schema sent to the API is strict and complete.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    """A source document (circular, filing, press release, article)."""

    source_id: str
    title: str
    url: str = ""
    text: str = ""
    published_at: datetime | None = None
    fetched_at: datetime = Field(default_factory=datetime.now)
    category: str = ""
    regulator: str = ""

    @property
    def content_hash(self) -> str:
        basis = f"{self.title}\n{self.url}\n{self.text}".encode("utf-8")
        return hashlib.sha256(basis).hexdigest()


# ---------------------------------------------------------------- LLM outputs


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Horizon(str, Enum):
    H0 = "H0"  # minutes to 1 day
    H1 = "H1"  # days to weeks
    H2 = "H2"  # months to quarters
    H3 = "H3"  # years
    NONE = "none"


class TriageResult(_Strict):
    is_market_relevant: bool
    playbook_id: str
    event_type: str
    materiality: int = Field(ge=0, le=100)
    horizon: Horizon
    status: Literal["proposal", "draft", "final", "effective", "news", "unverified"]
    primary_entities: list[str]
    summary: str
    why_it_matters: str
    needs_human_now: bool


class Fact(_Strict):
    claim: str
    source_quote: str  # exact words from the document supporting the claim


class Exposure(_Strict):
    entity: str  # company, sector, participant group or macro variable
    order: Literal["first", "second", "third"]
    direction: Literal["positive", "negative", "mixed", "unclear"]
    size: Literal["high", "medium", "low", "unclear"]
    rationale: str


class ResearchBrief(_Strict):
    headline: str
    status_note: str  # e.g. "Consultation paper, comments open till ..."
    facts: list[Fact]
    mechanism: str
    exposures: list[Exposure]
    participants: list[str]  # retail / FPI / DII / promoters / algos impact notes
    history_questions: list[str]  # what the Historian must look up (not answered here)
    skeptic_points: list[str]
    what_would_change_view: list[str]
    daily_life_anchor: str  # everyday situation the story can open from
    compliance_tier: Literal["E", "M", "RA"]


class VisualType(str, Enum):
    AVATAR = "AVATAR"
    CHART = "CHART"
    DOC_RECEIPT = "DOC_RECEIPT"
    ANIMATION = "ANIMATION"
    TEXT_CARD = "TEXT_CARD"
    BROLL = "BROLL"


class Scene(_Strict):
    id: str
    visual: VisualType
    narration: str  # Hindi (Devanagari) with English terms; [beat] marks pauses
    on_screen_text: str
    visual_spec: str  # what to show: chart series, document page, animation template


class ReelPlan(_Strict):
    series: str
    hook_text: str  # first-2-seconds on-screen hook
    scenes: list[Scene]
    caption: str
    hashtags: list[str]
    title_variants: list[str]  # three packaging options for testing
    disclosure: str
    sources: list[str]
    compliance_tier: Literal["E", "M", "RA"]
