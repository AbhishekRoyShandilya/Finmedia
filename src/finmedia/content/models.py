"""Structured outputs for the content engine. Every format renders ONE Research Object; numbers must trace to it."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..models import VisualType

Tier = Literal["E", "M", "RA"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class VisualCue(_Strict):
    visual: VisualType
    spec: str = Field(description="Exactly what to show: chart series, document section to highlight, animation")


class Chapter(_Strict):
    heading: str
    narration: str = Field(description="Hindi (Devanagari) with common English terms; [beat] marks a pause")
    on_screen_text: str
    visuals: list[VisualCue]


class YouTubeScript(_Strict):
    title_variants: list[str] = Field(description="Exactly three: Hinglish (Roman), Hindi (Devanagari), English")
    thumbnail_text: str
    hook: str = Field(description="First 15 seconds, spoken")
    chapters: list[Chapter]
    verdict_card: str = Field(description="Works / Doesn't work / Works only when ... - with its conditions")
    takeaway: str = Field(description="Something the viewer can use today (a checklist, a rule of thumb, a test)")
    description: str
    disclosure: str
    sources: list[str]
    compliance_tier: Tier


class Slide(_Strict):
    headline: str
    body: str
    visual_spec: str


class Carousel(_Strict):
    slides: list[Slide]
    caption: str
    hashtags: list[str]
    disclosure: str
    sources: list[str]
    compliance_tier: Tier


class NewsletterSection(_Strict):
    heading: str
    body: str


class Newsletter(_Strict):
    subject: str
    preheader: str
    intro: str
    sections: list[NewsletterSection]
    takeaway: str
    disclosure: str
    sources: list[str]
    compliance_tier: Tier
